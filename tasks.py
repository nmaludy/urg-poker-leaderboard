#!/usr/bin/env python
import contextlib
import datetime
import invoke
import jinja2
import json
import os
import re
import requests
import six
import subprocess
import yaml


@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)


def pretty_json(data):
    return json.dumps(data, indent=4, sort_keys=True)


def pprint_json(data):
    print(pretty_json(data))


PLACE_NUMBER_PATTERN = re.compile('(\\d+)')
NAME_PATTERN = re.compile('(.*?)( \\(\\d+\\))')


class PokerMavensClient(object):

    def __init__(self,
                 host,
                 password,
                 port=8087,
                 scheme='http',
                 verify_ssl=False,
                 api_path='/api'):
        self.host = host
        self.password = password
        self.port = port
        self.scheme = scheme
        self.verify_ssl = verify_ssl
        self.url = '{}://{}:{}{}'.format(scheme, host, port, api_path)

        self.session = requests.Session()
        self.session.verify = self.verify_ssl

    def post(self, command, parameters=None):
        params = parameters if parameters else {}
        params['Command'] = command
        params['Password'] = self.password
        params['JSON'] = 'Yes'
        response = self.session.post(self.url, data=params)
        response.raise_for_status()
        return response.json()

    def transpose_result(self, result):
        parsed = {'data': []}
        for k, v in six.iteritems(result):
            if isinstance(v, list):
                if parsed['data']:
                    if len(v) != len(parsed['data']):
                        raise ValueError('Error the length of key {} doesnt'
                                         'match the length of the other data elements: {}'
                                         '... parse so far: {}'.
                                         format(k, pretty_json(result), pretty_json(parsed)))
                    for i, d in enumerate(v):
                        parsed['data'][i][k] = d
                else:
                    for i, d in enumerate(v):
                        parsed['data'].append({k: d})
            else:
                parsed[k] = v
        return parsed

    def tournaments_results_list(self):
        result = self.post('TournamentsResults')
        return self.transpose_result(result)

    def tournaments_results_get(self, date, name):
        params = {}
        params['Date'] = date
        params['Name'] = name
        result = self.post('TournamentsResults', params)
        return self.parse_tournament_data(result['Data'])

    def parse_tournament_data(self, data):
        results = {}
        # data is a list of strings
        # each string is of the format: key=value
        # we want to extract these key/value pairs into dictionaries
        for d in data:
            # sometimes there are blank lines, just ignore these
            if not d:
                continue

            parts = d.split('=', 1)
            if len(parts) < 2:
                raise ValueError('Unable to parse tournament data element: {}'
                                 'In tournament data:\n{}'
                                 .format(d, pretty_json(data)))
            results[parts[0]] = parts[1]
        return results


class HugoPokerRepo(object):

    def __init__(self, c, repo_url, points_map):
        self.c = c
        self.repo_url = repo_url
        self.repo_name = repo_url.split('/')[-1].replace('.git', '')
        self.repo_path = '.'
        self.template_path = os.path.join(self.repo_path, 'templates', 'scores.j2.md')
        self.rendered_scores_path = os.path.join(self.repo_path, 'content', 'scores')
        self.points_map = points_map

    def clone_or_pull(self):
        # if the directory exists, pull, otherwise clone a fresh copy
        if os.path.isdir(self.repo_path):
            with pushd(self.repo_path):
                self.c.run("git checkout master")
                self.c.run("git pull")
        else:
            self.c.run("git clone {} {}".format(self.repo_url, self.repo_path))

    def tournament_results_to_scores(self, tournament_results):
        scores = {
            'scores': [],
            'points': {}
        }
        start_str = tournament_results['Start']
        start_dt = datetime.datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
        scores['name'] = tournament_results['Tournament']
        scores['date_year'] = datetime.datetime.strftime(start_dt, '%Y')
        scores['date_year_month'] = datetime.datetime.strftime(start_dt, '%Y-%m')
        scores['date_year_month_day'] = datetime.datetime.strftime(start_dt, '%Y-%m-%d')
        scores['date_time'] = start_str

        name_lower = scores['name'].lower()
        points_list = self.points_map['default']
        if name_lower in self.points_map:
            points_list = self.points_map[name_lower]
        for key, value in six.iteritems(tournament_results):
            if not key.startswith('Place'):
                continue
            place_num = int(PLACE_NUMBER_PATTERN.search(key).group(1))
            name = NAME_PATTERN.search(value).group(1)
            points = 0
            if place_num <= len(points_list):
                # places are 1 indexed, arrays are 0 indexed
                points = points_list[place_num - 1]
            scores['scores'].append({
                'place': place_num,
                'name': name,
                'points': points,
            })
            scores['points'][name] = points

        # sort scores by name then place for stability in case there are ties
        # then they will always come up the same
        scores['scores'] = sorted(scores['scores'], key=lambda s: s['name'])
        scores['scores'] = sorted(scores['scores'], key=lambda s: s['place'])
        return scores

    def add_points(self, points_lhs, points_rhs):
        total = {}
        # create a unique set of keys from both LHS and RHS
        for k in list(set(points_lhs.keys()) | set(points_rhs.keys())):
            total[k] = points_lhs.get(k, 0) + points_rhs.get(k, 0)
        return total

    def aggregate_scores_by_date(self, scores):
        agg = {}
        for s in scores:
            date = s['date_year_month_day']
            if date in agg:
                agg[date]['tournaments'].append(s)
                agg[date]['day_point_totals'] = self.add_points(agg[date]['day_point_totals'],
                                                                s['points'])
            else:
                agg[date] = {
                    'date_year': s['date_year'],
                    'date_year_month': s['date_year_month'],
                    'date_year_month_day': s['date_year_month_day'],
                    'tournaments': [s],
                    'day_point_totals': s['points'],
                }

        for k, v in six.iteritems(agg):
            # Sort tournaments by time played
            agg[k]['tournaments'] = sorted(agg[k]['tournaments'], key=lambda tr: tr['date_time'])
        return sorted(agg.values(), key=lambda tr: tr['date_year_month_day'])

    def accumulate_month_scores(self, agg_by_date):
        current_month = None
        current_month_points = {}
        # iterate for each date
        for day_agg in agg_by_date:
            if day_agg['date_year_month'] != current_month:
                current_month = day_agg['date_year_month']
                current_month_points = {}
            current_month_points = self.add_points(current_month_points,
                                                   day_agg['day_point_totals'])
            day_agg['month_point_totals'] = current_month_points
            month_scores = []
            for k, v in six.iteritems(current_month_points):
                month_scores.append({'name': k, 'points': v})

            # sort scores by name in case there are ties, then people always are arranged
            # in the same order
            # sort scores by points (highest at the top) so we can assign places
            month_scores = sorted(month_scores, key=lambda s: s['name'])
            month_scores = sorted(month_scores, key=lambda s: s['points'], reverse=True)
            for i, s in enumerate(month_scores):
                place = i + 1
                if i > 0 and month_scores[i-1]['points'] == s['points']:
                    # if we're in a long tie streak (multiple people with same score)
                    # then we want to mark all of them as tied for the same place
                    # we can do this by checking the previous place if it has a `t` in it
                    # if it does, then copy that forward
                    # else use the tied place marker from the current index
                    if 't' in str(month_scores[i-1]['place']):
                        place = month_scores[i-1]['place']
                    else:
                        place = "{}t".format(i)

                    # set the previous score to mark it as tied
                    month_scores[i-1]['place'] = place

                # assign the place to the current score
                s['place'] = place

            month_total_tournament = {
                'name': 'Month Point Totals',
                'scores': month_scores,
            }
            day_agg['tournaments'].append(month_total_tournament)

        return agg_by_date

    @staticmethod
    def jinja_render_file(template_path, context):
        path, filename = os.path.split(template_path)
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(path or './'))
        tmpl = env.get_template(filename)
        return tmpl.render(context)

    def render_day_scores_to_file(self, day_scores):
        data = HugoPokerRepo.jinja_render_file(self.template_path, day_scores)
        print(data)
        path = os.path.join(self.rendered_scores_path, day_scores['date_year_month_day'] + '.md')
        with open(path, 'w') as f:
            f.write(data)

    def is_change(self):
        # prints lines like:
        # M  content/scores/2019-11-07.md
        # A  content/scores/2019-12-15.md
        #
        # if nothing has changed, returns empty string
        return self.c.run('git status --porcelain')

    def commit_scores_and_push(self):
        print("Checking out master branch")
        self.c.run("git checkout master")
        print("Adding all data in content/")
        self.c.run('git add content')
        print("Committing to local repo...")
        t = datetime.datetime.now().isoformat()
        self.c.run('git commit -m "URG Poker Bot - Automatically updating scores on {}"'.format(t))
        self.c.run('git push origin master')
        print("Pushing local commits to origin..")

    def render_site_and_push(self):
        # copied from bin/publish_to_gh_pages.sh
        with pushd(self.repo_path):
            r = self.c.run('git rev-parse --quiet --verify render', warn=True)
            if r.exited:
                print("Checking out NEW render branch")
                self.c.run('git checkout -b render')
            else:
                print("Checking out EXISTING render branch")
                self.c.run('git checkout render')

            print("Deleting old publication")
            # rm -rf public
            if os.path.isdir('public'):
                shutil.rmtree('public')
            # mkdir public
            os.mkdir('public')

            print("Generating site")
            self.c.run('hugo')

            print("Committing public/ to render branch")
            self.c.run('git commit -m "URG Poker Bot - Auto rendering site on {}"'.format(t))

            print("Updating gh-pages branch")
            self.c.run('git subtree push --prefix public origin gh-pages')


@invoke.task
def build(c):
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    client = PokerMavensClient(config['poker_mavens']['host'],
                               config['poker_mavens']['password'])
    hugo_repo = HugoPokerRepo(c,
                              config['git_repo'],
                              config['points'])
    hugo_repo.clone_or_pull()

    results_list = client.tournaments_results_list()
    scores_list = []
    for r in results_list['data']:
        tr = client.tournaments_results_get(r['Date'], r['Name'])
        pprint_json(tr)
        scores = hugo_repo.tournament_results_to_scores(tr)
        pprint_json(scores)
        scores_list.append(scores)

    agg = hugo_repo.aggregate_scores_by_date(scores_list)
    pprint_json(agg)

    agg = hugo_repo.accumulate_month_scores(agg)
    pprint_json(agg)

    for a in agg:
        hugo_repo.render_day_scores_to_file(a)

    changed = hugo_repo.is_change()
    if changed:
        print("files have changed, committing, rendering and pushing")
        print(changed)
        print("end changed")
        hugo_repo.commit_scores_and_push()
        hugo_repo.render_site_and_push()
    else:
        print("nothing changed, not doing anything")

    # TODO - advanced logging
    exit(0)
