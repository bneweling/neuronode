# setup.ps1 - Wrapper für das neue Skript in scripts/setup/

$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
& "$ScriptDir\scripts\setup\setup.ps1" @args
