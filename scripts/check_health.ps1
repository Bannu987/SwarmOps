param (
    [string]$BaseUrl = "http://localhost:8000"
)

$targetUrl = "$BaseUrl/health"
Write-Host "Checking SwarmOps Backend Health at: $targetUrl" -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri $targetUrl -Method Get -ErrorAction Stop
    Write-Host "Success: Health check passed!" -ForegroundColor Green
    Write-Host (ConvertTo-Json $response -Depth 4) -ForegroundColor Gray
}
catch {
    Write-Host "Error: Health check failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $body = $reader.ReadToEnd()
        Write-Host "Response Body: $body" -ForegroundColor Red
    }
    exit 1
}
