param(
  [string]$CertName = "Casino Bonus Monitor",
  [string]$ExePath = ""
)

if (-not $ExePath) {
  $ExePath = Join-Path $PSScriptRoot "..\CasinoBot.exe"
}

if (-not (Test-Path $ExePath)) {
  Write-Error "EXE not found at: $ExePath"
  Write-Error "Build first with: npm run build"
  exit 1
}

Write-Output "Signing: $ExePath"

# Find the cert
$cert = Get-ChildItem "Cert:\CurrentUser\My" | Where-Object { $_.FriendlyName -eq "$CertName Code Signing" } | Select-Object -First 1

if (-not $cert) {
  Write-Error "Certificate not found. Run .\cert\gen-cert.ps1 first."
  exit 1
}

Write-Output "  Using cert: $($cert.Subject) (thumbprint: $($cert.Thumbprint))"

# Try with timestamp first, fall back to without
try {
  Set-AuthenticodeSignature -FilePath $ExePath -Certificate $cert -TimestampServer "http://timestamp.digicert.com" -ErrorAction Stop
} catch {
  Write-Output "  Timestamp server unreachable, signing without timestamp..."
  Set-AuthenticodeSignature -FilePath $ExePath -Certificate $cert -ErrorAction Stop
}

$sig = Get-AuthenticodeSignature -FilePath $ExePath
Write-Output "  Signature status: $($sig.Status)"

if ($sig.Status -eq "Valid") {
  Write-Output "✅ CasinoBot.exe signed successfully!"
} else {
  Write-Output "❌ Signature status: $($sig.Status)"
  exit 1
}
