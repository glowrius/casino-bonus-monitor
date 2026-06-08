param(
  [switch]$SkipSign = $false,
  [string]$Version = "2.0.0"
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path "$root\.."
$srcDir = "$projectRoot\src"
$outputDir = "$projectRoot\build"

if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir -Force | Out-Null }

Write-Output ""
Write-Output "═══════════════════════════════════════"
Write-Output "  Casino Bonus Monitor - Build v$Version"
Write-Output "═══════════════════════════════════════"
Write-Output ""

# 1. Install dependencies
Write-Output "[1/4] Installing dependencies..."
Set-Location $srcDir
npm install --silent 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "npm install failed"; exit 1 }

# 2. Pkg build
Write-Output "[2/4] Building EXE with @yao-pkg/pkg..."
npx @yao-pkg/pkg -t node22-win-x64 index.js -o "$projectRoot\CasinoBot.exe" 2>&1
if ($LASTEXITCODE -ne 0 -and -not (Test-Path "$projectRoot\CasinoBot.exe")) { Write-Error "pkg build failed"; exit 1 }

# 3. Add icon + metadata
Write-Output "[3/4] Adding icon and metadata..."
$rcedit = "$env:APPDATA\npm\node_modules\rcedit\bin\rcedit-x64.exe"
if (Test-Path $rcedit) {
  & $rcedit "$projectRoot\CasinoBot.exe" --set-icon "$projectRoot\icon.ico" `
    --set-version-string "FileDescription" "Casino Bonus Monitor" `
    --set-version-string "ProductName" "Casino Bonus Monitor" `
    --set-version-string "ProductVersion" $Version `
    --set-version-string "FileVersion" $Version `
    --set-version-string "LegalCopyright" "(c) glowrius"
}

# 4. Sign
if (-not $SkipSign) {
  Write-Output "[4/4] Signing executable..."
  & "$root\cert\sign.ps1" -ExePath "$projectRoot\CasinoBot.exe" 2>&1
  $sig = Get-AuthenticodeSignature "$projectRoot\CasinoBot.exe"
  if ($sig.Status -eq "Valid") {
    Write-Output "  ✅ Signed (Valid)"
  } else {
    Write-Output "  ⚠ Signature: $($sig.Status)"
  }
} else {
  Write-Output "[4/4] Skipped (--SkipSign)"
}

$size = (Get-Item "$projectRoot\CasinoBot.exe").Length / 1MB
Write-Output ""
Write-Output "═══════════════════════════════════════"
Write-Output "  CasinoBot.exe built - $([math]::Round($size,1)) MB"
Write-Output "═══════════════════════════════════════"
