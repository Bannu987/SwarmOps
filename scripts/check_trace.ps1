param (
    [string]$BaseUrl = "http://localhost:8000",
    [string]$TraceId = "",
    [string]$AuthToken = ""
)

if ([string]::IsNullOrEmpty($TraceId)) {
    Write-Host "Error: A valid TraceId parameter is required." -ForegroundColor Red
    Write-Host "Usage: .\check_trace.ps1 -BaseUrl http://localhost:8000 -TraceId <trace-uuid>" -ForegroundColor Yellow
    exit 1
}

# Try to find auth token if not provided
if ([string]::IsNullOrEmpty($AuthToken)) {
    if (Test-Path "token.txt") {
        $AuthToken = (Get-Content "token.txt").Trim()
        Write-Host "Loaded auth token from local token.txt" -ForegroundColor Yellow
    } elseif (Test-Path "../token.txt") {
        $AuthToken = (Get-Content "../token.txt").Trim()
        Write-Host "Loaded auth token from parent token.txt" -ForegroundColor Yellow
    } elseif ($env:SWARMOPS_AUTH_TOKEN) {
        $AuthToken = $env:SWARMOPS_AUTH_TOKEN
        Write-Host "Loaded auth token from environment variable SWARMOPS_AUTH_TOKEN" -ForegroundColor Yellow
    }
}

$targetUrl = "$BaseUrl/api/runs/$TraceId"
Write-Host "Checking SwarmOps Run Trace Recovery at: $targetUrl" -ForegroundColor Cyan

# Configure Headers
$headers = @{}
if (![string]::IsNullOrEmpty($AuthToken)) {
    $cleanToken = $AuthToken -replace "Bearer\s+", ""
    $headers.Add("Authorization", "Bearer $cleanToken")
    Write-Host "Authorization Bearer token attached." -ForegroundColor Gray
} else {
    Write-Host "Warning: No auth token provided. Request will fail if auth is enforced." -ForegroundColor Yellow
}

try {
    $response = Invoke-RestMethod -Uri $targetUrl -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "Success: Run trace recovery query succeeded!" -ForegroundColor Green
    
    Write-Host "`n=== Trace Overview ===" -ForegroundColor Cyan
    Write-Host "Trace ID: $($response.trace_id)" -ForegroundColor Gray
    Write-Host "Status: $($response.status)" -ForegroundColor Gray
    Write-Host "Model Name: $($response.model_name)" -ForegroundColor Gray
    Write-Host "Latency: $($response.latency_ms) ms" -ForegroundColor Gray
    
    if ($null -ne $response.active_flags) {
        Write-Host "`n=== Active Flags Snapshot ===" -ForegroundColor Cyan
        Write-Host (ConvertTo-Json $response.active_flags -Depth 4) -ForegroundColor Gray
    }

    if ($null -ne $response.replay_snapshot) {
        $snapshot = $response.replay_snapshot
        Write-Host "`n=== Replay Snapshot Convenience Fields ===" -ForegroundColor Cyan
        Write-Host "Final Answer Available: $($snapshot.final_answer_available)" -ForegroundColor Gray
        Write-Host "Confidence Score: $($snapshot.confidence)" -ForegroundColor Gray
        Write-Host "Action Plan Created: $($snapshot.action_plan_created)" -ForegroundColor Gray
        Write-Host "Agents Consulted: $($snapshot.agents_consulted)" -ForegroundColor Gray
        Write-Host "Title: $($snapshot.title)" -ForegroundColor Gray
        Write-Host "Priority Score: $($snapshot.priority_score)" -ForegroundColor Gray
        Write-Host "Priority Bucket: $($snapshot.priority_bucket)" -ForegroundColor Gray
        Write-Host "Retrieved Memories (Count): $($snapshot.retrieved_memories.Count)" -ForegroundColor Gray
        
        Write-Host "`n=== Executive Summary ===" -ForegroundColor Cyan
        Write-Host $snapshot.executive_summary -ForegroundColor Gray
    } else {
        Write-Host "`nReplay Snapshot: [No replay snapshot available yet - run might be in_progress or failed]" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Error: Failed to retrieve run trace recovery data!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $body = $reader.ReadToEnd()
        Write-Host "Response Body: $body" -ForegroundColor Red
    }
    exit 1
}
