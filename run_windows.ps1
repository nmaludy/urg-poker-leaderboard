Write-Output "Changing to script directory: $PSScriptRoot"
Set-Location $PSScriptRoot
Write-Output "Activating virtualenv"
.\venv\Scripts\activate.bat
Write-Output "Running poker_mavens.py"
invoke build
exit 0
