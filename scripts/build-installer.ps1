param(
  [string]$Version = "2.0.0"
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path "$root\.."
$iscc = "C:\Users\GLOW\AppData\Local\Programs\Inno Setup 6\ISCC.exe"

if (-not (Test-Path $iscc)) {
  Write-Error "ISCC.exe not found. Install Inno Setup 6 first."
  exit 1
}

if (-not (Test-Path "$projectRoot\CasinoBot.exe")) {
  Write-Error "CasinoBot.exe not found. Run scripts\build.ps1 first."
  exit 1
}

if (-not (Test-Path "$projectRoot\build")) {
  New-Item -ItemType Directory -Path "$projectRoot\build" -Force | Out-Null
}

Write-Output ""
Write-Output "═══════════════════════════════════════"
Write-Output "  Building Installer v$Version"
Write-Output "═══════════════════════════════════════"
Write-Output ""

Set-Location $root

# Update version in .iss
(Get-Content "setup.iss") -replace '#define MyAppVersion ".*"', "#define MyAppVersion `"$Version`"" | Set-Content "setup.iss"

# Compile
& $iscc "setup.iss" /Q 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Error "Inno Setup compilation failed (exit: $LASTEXITCODE)"
  exit 1
}

$installer = Get-ChildItem "$projectRoot\build\CasinoBot-Setup-$Version.exe"
if ($installer) {
  $size = $installer.Length / 1MB
  Write-Output ""
  Write-Output "═══════════════════════════════════════"
  Write-Output "  Installer built: $($installer.Name)"
  Write-Output "  Size: $([math]::Round($size,1)) MB"
  Write-Output "═══════════════════════════════════════"
} else {
  Write-Error "Installer not found after compilation"
  exit 1
}
