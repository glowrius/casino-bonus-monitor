param(
  [string]$CertName = "Casino Bonus Monitor",
  [string]$CertFile = "CasinoBot"
)

$certStore = "Cert:\CurrentUser\My"
$exportPath = Join-Path $PSScriptRoot "..\$CertFile.cer"
$signTool = Join-Path $PSScriptRoot "sign.ps1"

Write-Output "Generating self-signed code signing certificate..."
Write-Output "  Subject:  CN=$CertName"
Write-Output "  Store:    $certStore"
Write-Output ""

$cert = New-SelfSignedCertificate `
  -Subject "CN=$CertName" `
  -FriendlyName "$CertName Code Signing" `
  -Type CodeSigningCert `
  -CertStoreLocation $certStore `
  -KeyExportPolicy Exportable `
  -KeyLength 2048 `
  -NotAfter (Get-Date).AddYears(10)

$thumbprint = $cert.Thumbprint
Write-Output "Certificate generated:"
Write-Output "  Thumbprint: $thumbprint"
Write-Output "  Expires:    $($cert.NotAfter)"
Write-Output ""

# Export the public cert for distribution
Export-Certificate -Cert $cert -FilePath $exportPath -Type CERT | Out-Null
Write-Output "Exported public cert to: $exportPath"
Write-Output ""

Write-Output "Installing cert to Trusted Publishers (so Windows trusts it)..."
$trustStore = "Cert:\LocalMachine\TrustedPublisher"
$existing = Get-ChildItem $trustStore | Where-Object { $_.Thumbprint -eq $thumbprint }
if (-not $existing) {
  $target = Join-Path $trustStore "$thumbprint"
  $null = New-Item $target -Force
  Set-ItemProperty $target -Name "(default)" -Value $cert.RawData -Type Binary
  Write-Output "  Installed to Trusted Publishers"
} else {
  Write-Output "  Already in Trusted Publishers"
}

# Also trust locally (CurrentUser)
$cuTrustStore = "Cert:\CurrentUser\TrustedPublisher"
$cuExisting = Get-ChildItem $cuTrustStore | Where-Object { $_.Thumbprint -eq $thumbprint }
if (-not $cuExisting) {
  $cuTarget = Join-Path $cuTrustStore "$thumbprint"
  $null = New-Item $cuTarget -Force
  Set-ItemProperty $cuTarget -Name "(default)" -Value $cert.RawData -Type Binary
  Write-Output "  Installed to CurrentUser\\TrustedPublisher"
} else {
  Write-Output "  Already in CurrentUser\\TrustedPublisher"
}

Write-Output ""
Write-Output "Certificate ready for signing."
Write-Output "Run .\cert\sign.ps1 to sign CasinoBot.exe"
