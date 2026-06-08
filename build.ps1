param(
  [switch]$SkipSign = $false
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Output "═══════════════════════════════════════"
Write-Output "  Casino Bonus Monitor - Build Script"
Write-Output "═══════════════════════════════════════"
Write-Output ""

# 1. Pkg build
Write-Output "[1/3] Building EXE with @yao-pkg/pkg..."
npx @yao-pkg/pkg -t node22-win-x64 index.js -o CasinoBot.exe
if ($LASTEXITCODE -ne 0) { Write-Error "Build failed"; exit 1 }
Write-Output "  ✅ Built CasinoBot.exe"
Write-Output ""

# 2. Add icon + metadata
Write-Output "[2/3] Adding icon and metadata..."
$rcedit = "$env:APPDATA\npm\node_modules\rcedit\bin\rcedit-x64.exe"
if (Test-Path $rcedit) {
  & $rcedit "CasinoBot.exe" --set-icon "icon.ico" `
    --set-version-string "FileDescription" "Casino Bonus Monitor" `
    --set-version-string "ProductName" "Casino Bonus Monitor" `
    --set-version-string "LegalCopyright" "(c) glowrius"
  Write-Output "  ✅ Icon and metadata applied"
} else {
  Write-Output "  ⚠ rcedit not found, skipping icon"
}
Write-Output ""

# 3. Sign
if (-not $SkipSign) {
  Write-Output "[3/3] Signing executable..."
  & "$root\cert\sign.ps1" -ExePath "$root\CasinoBot.exe"
  if ($LASTEXITCODE -ne 0) { Write-Output "  ⚠ Signing failed (cert may not exist)" }
} else {
  Write-Output "[3/3] Skipped (--SkipSign)"
}

Write-Output ""
$size = (Get-Item "CasinoBot.exe").Length / 1MB
Write-Output "═══════════════════════════════════════"
Write-Output "  CasinoBot.exe ready - $([math]::Round($size,1)) MB"
Write-Output "═══════════════════════════════════════"
