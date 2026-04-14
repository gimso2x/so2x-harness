param(
  [string]$Project = ".",
  [string]$Platform = "claude",
  [string]$Preset = "general"
)

$ErrorActionPreference = "Stop"
$RepoUrl = if ($env:SO2X_REPO_URL) { $env:SO2X_REPO_URL } else { "https://github.com/gimso2x/so2x-harness.git" }
$RepoRef = if ($env:SO2X_REPO_REF) { $env:SO2X_REPO_REF } else { "main" }
$TempRoot = $null
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Info($msg) {
  Write-Host "[so2x-harness] $msg"
}

function Fail($msg) {
  Write-Host "[so2x-harness] ERROR: $msg" -ForegroundColor Red
  if ($TempRoot -and (Test-Path $TempRoot)) { Remove-Item -Recurse -Force $TempRoot -ErrorAction SilentlyContinue }
  exit 1
}

function Resolve-RootDir {
  if ($Root -and (Test-Path (Join-Path $Root "scripts/apply.py"))) {
    return $Root
  }

  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Fail "raw 설치에는 git이 필요합니다. git을 설치하거나 repo를 clone한 뒤 로컬 install.ps1를 실행해 주세요."
  }

  $script:TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("so2x-harness-" + [System.Guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Path $script:TempRoot -Force | Out-Null
  Info "bootstrap source를 임시 디렉터리에 내려받습니다."
  git clone --depth 1 --branch $RepoRef $RepoUrl (Join-Path $script:TempRoot "repo") | Out-Null
  return (Join-Path $script:TempRoot "repo")
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

$ResolvedRoot = Resolve-RootDir
$projectAbs = (Resolve-Path $Project).Path

Info "project=$projectAbs"
Info "platform=$Platform"
Info "preset=$Preset"
Info "python=$pythonCmd"
Info "source=$ResolvedRoot"

& $pythonCmd "$ResolvedRoot/scripts/apply.py" --project $projectAbs --platform $Platform --preset $Preset

Info "설치가 끝났습니다. 확인하려면 아래를 실행하세요:"
Info "  $pythonCmd $ResolvedRoot/scripts/doctor.py --project $projectAbs"

if ($TempRoot -and (Test-Path $TempRoot)) {
  Remove-Item -Recurse -Force $TempRoot -ErrorAction SilentlyContinue
}
