param(
  [string]$Project = ".",
  [string]$Platform = "claude"
)

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$Root/scripts/apply.py" --project $Project --platform $Platform
