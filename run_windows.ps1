Write-Output "Changing to script directory: $PSScriptRoot"
Set-Location $PSScriptRoot
Write-Output "Activating virtualenv"
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser -Force
.\venv\Scripts\activate.ps1
Write-Output "Running poker_mavens.py"
invoke build
exit 0
