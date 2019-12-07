+++
author = "URG Poker Bot"
author_url = "urgpoker.com"
categories = ["{{ date_year }}", "{{ date_year_month }}"]
date = "{{ date_year_month_day }}"
title = "Scores for {{ date_year_month_day }}"
type = "post"
+++

{%- for t in tournaments %}
# {{ t.name }}

| Place | User | Points |
|-------|------|--------|
{%- for s in t.scores %}
| {{ s.place }} | {{ s.name }} | {{ "{:,}".format(s.points) }} |
{%- endfor %}
{% endfor %}
