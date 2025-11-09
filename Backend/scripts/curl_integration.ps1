# PowerShell 5.1-compatible integration script

$ErrorActionPreference = "Stop"

function Get-EnvOrDefault {
    param([string]$Name, [string]$Default)
    $v = [System.Environment]::GetEnvironmentVariable($Name)
    if (-not [string]::IsNullOrEmpty($v)) { return $v }
    return $Default
}

# --- Paths & defaults ---
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$GoldenFile  = Get-EnvOrDefault 'GOLDEN_FILE'  (Join-Path $ScriptDir '..\tests\data\golden_employee.json')
$BaseUrl     = Get-EnvOrDefault 'BASE_URL'     'http://127.0.0.1:8000'
$UpdatedLast = Get-EnvOrDefault 'UPDATED_LAST' 'IntegrationTest'

if (-not (Test-Path $GoldenFile)) { throw "Golden data file not found: $GoldenFile" }

# --- Load golden JSON via Python ---
$py = @"
import json, sys, io
with io.open(sys.argv[1], 'r', encoding='utf-8') as f:
    print(json.dumps(json.load(f)))
"@
$Golden = & python -c $py $GoldenFile
$GoldenData = $Golden | ConvertFrom-Json

$EmpNo       = [string]$GoldenData.employee.emp_no
$GoldenFirst = [string]$GoldenData.employee.first_name
$GoldenLast  = [string]$GoldenData.employee.last_name
$WrUser      = 'admin'
$WrPass      = [string]$GoldenData.users.admin.password
$RdUser      = 'analyst'
$RdPass      = [string]$GoldenData.users.analyst.password

function Invoke-CurlJson {
    param(
        [string]$User, [string]$Pass, [string]$Method, [string]$Url,
        [hashtable]$Headers = @{}, [string]$Body = ''
    )
    $args = @('-sS', '-u', "$User`:$Pass", '-X', $Method, $Url,
              '-H', 'accept: application/json', '-w', "`n%{http_code}")
    foreach ($k in $Headers.Keys) { $args += @('-H', "$($k): $($Headers[$k])") }

    if ($Body -ne '') {
        # Send JSON through stdin so Windows curl doesn’t mangle quotes
        $args += @('-H', 'Content-Type: application/json', '--data-binary', '@-')
        $result = $Body | & curl.exe @args
    } else {
        $result = & curl.exe @args
    }

    $lines  = $result -split "`r?`n"
    $status = $lines[-1].Trim()
    $body   = if ($lines.Length -gt 1) { ($lines[0..($lines.Length-2)] -join "`n") } else { '' }
    [pscustomobject]@{ Status = $status; Body = $body }
}

function Require-Status { param($Expected,$Actual,$Body)
    if ("$Expected" -ne "$Actual") { throw "Expected HTTP $Expected but got $Actual`nResponse: $Body" }
}

Write-Host "Starting writer session for $WrUser..."
$r = Invoke-CurlJson $WrUser $WrPass 'POST' "$BaseUrl/sessions/start"
Require-Status 200 $r.Status $r.Body
$SessionId = (ConvertFrom-Json $r.Body).session_id

Write-Host "Verifying employee $EmpNo matches golden data..."
$r = Invoke-CurlJson $WrUser $WrPass 'GET' "$BaseUrl/employees/$EmpNo" @{ 'X-Session-Id' = $SessionId }
Require-Status 200 $r.Status $r.Body
$emp = $r.Body | ConvertFrom-Json
if ($emp.first_name -ne $GoldenFirst -or $emp.last_name -ne $GoldenLast) {
    throw "Golden mismatch: expected $GoldenFirst $GoldenLast, got $($emp.first_name) $($emp.last_name)"
}

Write-Host "Updating employee $EmpNo last name to $UpdatedLast..."
$payload = @{ last_name = $UpdatedLast } | ConvertTo-Json -Compress
$r = Invoke-CurlJson $WrUser $WrPass 'PUT' "$BaseUrl/employees/$EmpNo/last-name" @{ 'X-Session-Id' = $SessionId } $payload
Require-Status 200 $r.Status $r.Body

$r = Invoke-CurlJson $WrUser $WrPass 'GET' "$BaseUrl/employees/$EmpNo" @{ 'X-Session-Id' = $SessionId }
Require-Status 200 $r.Status $r.Body
$emp = $r.Body | ConvertFrom-Json
if ($emp.last_name -ne $UpdatedLast) { throw "Update failed: expected $UpdatedLast, got $($emp.last_name)" }

Write-Host "Ensuring read-only user cannot perform updates..."
$r = Invoke-CurlJson $RdUser $RdPass 'POST' "$BaseUrl/sessions/start"
Require-Status 200 $r.Status $r.Body
$RdSession = (ConvertFrom-Json $r.Body).session_id

$payload = @{ last_name = 'ShouldFail' } | ConvertTo-Json -Compress
$r = Invoke-CurlJson $RdUser $RdPass 'PUT' "$BaseUrl/employees/$EmpNo/last-name" @{ 'X-Session-Id' = $RdSession } $payload
Require-Status 403 $r.Status $r.Body

Write-Host "Reverting employee $EmpNo last name to $GoldenLast..."
$payload = @{ last_name = $GoldenLast } | ConvertTo-Json -Compress
$r = Invoke-CurlJson $WrUser $WrPass 'PUT' "$BaseUrl/employees/$EmpNo/last-name" @{ 'X-Session-Id' = $SessionId } $payload
Require-Status 200 $r.Status $r.Body

Invoke-CurlJson $WrUser $WrPass 'POST' "$BaseUrl/sessions/end" @{ 'X-Session-Id' = $SessionId } | Out-Null
Invoke-CurlJson $RdUser $RdPass 'POST' "$BaseUrl/sessions/end" @{ 'X-Session-Id' = $RdSession } | Out-Null

Write-Host "Integration checks completed successfully."
