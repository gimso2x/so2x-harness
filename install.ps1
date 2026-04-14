param(
  [string]$Project = ".",
  [string]$Platform = "claude",
  [string]$Preset = "general"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Info($msg) {
  Write-Host "[so2x-harness] $msg"
}

function Fail($msg) {
  Write-Host "[so2x-harness] ERROR: $msg" -ForegroundColor Red
  exit 1
}

$pythonCmd = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
  $pythonCmd = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $pythonCmd = "python"
} else {
  Fail "python3 또는 python을 찾지 못했습니다. Python을 설치한 뒤 다시 실행해 주세요."
}

if (-not (Test-Path $Project -PathType Container)) {
  Fail "대상 프로젝트 디렉터리가 없습니다: $Project"
}

if ($Platform -ne "claude") {
  Fail "현재 지원하지 않는 platform입니다: $Platform (지원: claude)"
}

if (($Preset -ne "general") -and ($Preset -ne "nextjs")) {
  Fail "현재 지원하지 않는 preset입니다: $Preset (지원: general, nextjs)"
}

$projectAbs = (Resolve-Path $Project).Path

Info "project=$projectAbs"
Info "platform=$Platform"
Info "preset=$Preset"
Info "python=$pythonCmd"

& $pythonCmd "$Root/scripts/apply.py" --project $projectAbs --platform $Platform --preset $Preset

Info "설치가 끝났습니다. 확인하려면 아래를 실행하세요:"
Info "  $pythonCmd $Root/scripts/doctor.py --project $projectAbs"
