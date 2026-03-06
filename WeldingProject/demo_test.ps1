# Demo test script: Register -> Login -> Setup Wizard (PUT shop-settings) -> GET staff/items
# Run: powershell -ExecutionPolicy Bypass -File demo_test.ps1
# Ensure backend: cd WeldingProject; python manage.py runserver 127.0.0.1:8000
$base = "http://127.0.0.1:8000/api"
$ErrorActionPreference = "Stop"

function Test-Endpoint {
    param($Method, $Url, $Body, $Token)
    $headers = @{ "Content-Type" = "application/json" }
    if ($Token) { $headers["Authorization"] = "Bearer $Token" }
    try {
        $params = @{ Uri = $Url; Method = $Method; Headers = $headers }
        if ($Body) { $params["Body"] = ($Body | ConvertTo-Json -Compress) }
        $r = Invoke-RestMethod @params
        return @{ ok = $true; data = $r }
    } catch {
        $status = $null
        if ($_.Exception.Response) { $status = $_.Exception.Response.StatusCode.value__ }
        $body = $null
        try { if ($_.Exception.Response) { $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()); $body = $reader.ReadToEnd() } } catch {}
        return @{ ok = $false; status = $status; body = $body }
    }
}

Write-Host "`n=== 1. Health (optional) ===" -ForegroundColor Cyan
try {
    $h = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health/" -Method Get -TimeoutSec 2
    Write-Host "OK: $($h | ConvertTo-Json -Compress)"
} catch {
    Write-Host "Backend not running? Start: cd WeldingProject; python manage.py runserver" -ForegroundColor Yellow
    Write-Host "Then run this script again. Continuing to try API anyway..."
}

Write-Host "`n=== 2. Register (first user) ===" -ForegroundColor Cyan
$regBody = @{
    email = "demo@test.local"
    phone_number = "09123456789"
    shop_name = "Demo Shop"
    password = "demo1234"
    password_confirm = "demo1234"
}
$reg = Test-Endpoint -Method Post -Url "$base/core/register/" -Body $regBody
if (-not $reg.ok) {
    if ($reg.status -eq 400) { Write-Host "Register 400 (maybe user exists): $($reg.body)" -ForegroundColor Yellow }
    else { Write-Host "Register failed: $($reg.status) $($reg.body)" -ForegroundColor Red }
} else {
    Write-Host "Register OK: $($reg.data.message)"
    Write-Host "  can_login_now: $($reg.data.can_login_now)"
    if ($reg.data.access) { Write-Host "  (tokens returned in response)" }
}

Write-Host "`n=== 3. Login ===" -ForegroundColor Cyan
$loginBody = @{ login = "09123456789"; password = "demo1234"; country_code = "+95" }
$login = Test-Endpoint -Method Post -Url "$base/core/auth/login/" -Body $loginBody
if (-not $login.ok) {
    Write-Host "Login failed: $($login.status) $($login.body)" -ForegroundColor Red
    exit 1
}
$token = $login.data.access
Write-Host "Login OK, token received."

Write-Host "`n=== 4. GET shop-settings ===" -ForegroundColor Cyan
$getShop = Test-Endpoint -Method Get -Url "$base/core/shop-settings/" -Token $token
if (-not $getShop.ok) {
    Write-Host "GET shop-settings failed: $($getShop.status)" -ForegroundColor Red
} else {
    Write-Host "GET shop-settings OK: shop_name=$($getShop.data.shop_name), setup_wizard_done=$($getShop.data.setup_wizard_done)"
}

Write-Host "`n=== 5. PUT shop-settings (Setup Wizard) ===" -ForegroundColor Cyan
$putBody = @{ business_category = "general"; currency = "MMK"; setup_wizard_done = $true }
$putShop = Test-Endpoint -Method Put -Url "$base/core/shop-settings/" -Body $putBody -Token $token
if (-not $putShop.ok) {
    Write-Host "PUT shop-settings failed: $($putShop.status) $($putShop.body)" -ForegroundColor Red
} else {
    Write-Host "PUT shop-settings OK (no 403). Setup wizard complete."
}

Write-Host "`n=== 6. GET staff/items (with trailing slash) ===" -ForegroundColor Cyan
$items1 = Test-Endpoint -Method Get -Url "$base/staff/items/" -Token $token
if (-not $items1.ok) {
    Write-Host "GET staff/items/ failed: $($items1.status) $($items1.body)" -ForegroundColor Red
} else {
    $list = if ($items1.data -is [array]) { $items1.data } else { $items1.data.results }
    if (-not $list) { $list = @() }
    Write-Host "GET staff/items/ OK: $($list.Count) items"
}

Write-Host "`n=== 7. GET staff/items (no trailing slash) ===" -ForegroundColor Cyan
$items2 = Test-Endpoint -Method Get -Url "$base/staff/items" -Token $token
if (-not $items2.ok) {
    Write-Host "GET staff/items failed: $($items2.status)" -ForegroundColor Red
} else {
    $list2 = if ($items2.data -is [array]) { $items2.data } else { $items2.data.results }
    if (-not $list2) { $list2 = @() }
    Write-Host "GET staff/items OK: $($list2.Count) items (no 404)"
}

Write-Host "`n=== Demo test done ===" -ForegroundColor Green
