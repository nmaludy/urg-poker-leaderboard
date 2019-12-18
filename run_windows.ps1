Write-Output "Changing to script directory: $PSScriptRoot"
Set-Location $PSScriptRoot
Write-Output "Activating virtualenv"
.\venv\Scripts\activate.ps1
Write-Output "Running poker_mavens.py"
python .\poker_mavens.py
exit 0