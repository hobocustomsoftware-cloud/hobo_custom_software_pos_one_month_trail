# PowerShell script to find local IP for Expo Go testing
# Run: .\scripts\find-ip.ps1

$adapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*"
} | Select-Object InterfaceAlias, IPAddress

if ($adapters.Count -eq 0) {
    Write-Host "❌ No local IP address found" -ForegroundColor Red
    exit 1
}

Write-Host "`n📱 Expo Go Testing - Local IP Addresses:`n" -ForegroundColor Cyan

foreach ($adapter in $adapters) {
    Write-Host "  $($adapter.InterfaceAlias): $($adapter.IPAddress)"
}

$primaryIp = $adapters[0].IPAddress
Write-Host "`n✅ Primary IP: $primaryIp`n" -ForegroundColor Green

Write-Host "📝 Update app.json:`n" -ForegroundColor Yellow
Write-Host '  "extra": {'
Write-Host "    `"apiUrl`": `"http://$primaryIp:8000/api`","
Write-Host "    `"localIp`": `"$primaryIp`","
Write-Host "    ..."
Write-Host "  }`n"

Write-Host "🔧 Or set environment variable:" -ForegroundColor Yellow
Write-Host "  `$env:EXPO_LOCAL_IP='$primaryIp'; npm run expo:start`n"
