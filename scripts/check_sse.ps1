param (
    [string]$BaseUrl = "http://localhost:8000",
    [string]$AuthToken = "",
    [string]$Message = "Verify SSE connectivity and agent responses"
)

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

$targetUrl = "$BaseUrl/api/chat/stream"
Write-Host "Initiating streaming test at: $targetUrl" -ForegroundColor Cyan
Write-Host "Message: $Message" -ForegroundColor Cyan

# Prepare HTTP Request
$client = New-Object System.Net.Http.HttpClient
$client.Timeout = [System.TimeSpan]::FromMinutes(5)

# Add headers
if (![string]::IsNullOrEmpty($AuthToken)) {
    # Strip Bearer prefix if user copied it literally
    $cleanToken = $AuthToken -replace "Bearer\s+", ""
    $client.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", $cleanToken)
    Write-Host "Authorization Bearer token attached." -ForegroundColor Gray
} else {
    Write-Host "Warning: No auth token provided. Stream might fail if endpoint requires auth." -ForegroundColor Yellow
}

$payload = @{
    message = $Message
    conversation_id = "sse-test-run-" + (New-Guid).Guid.Substring(0, 8)
}
$jsonPayload = $payload | ConvertTo-Json
$content = New-Object System.Net.Http.StringContent($jsonPayload, [System.Text.Encoding]::UTF8, "application/json")

try {
    # Post request async to stream response
    $responseTask = $client.PostAsync($targetUrl, $content)
    $response = $responseTask.GetAwaiter().GetResult()

    Write-Host "Response Status Code: $($response.StatusCode) ($([int]$response.StatusCode))" -ForegroundColor Gray
    
    if (!$response.IsSuccessStatusCode) {
        $errorBody = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        Write-Host "Error: Stream failed to start!" -ForegroundColor Red
        Write-Host "Details: $errorBody" -ForegroundColor Red
        exit 1
    }

    $contentType = $response.Content.Headers.ContentType.ToString()
    Write-Host "Content-Type: $contentType" -ForegroundColor Gray
    
    if ($contentType -notmatch "text/event-stream") {
        Write-Host "Warning: Response is not text/event-stream! Might be buffered." -ForegroundColor Yellow
    }

    $stream = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
    $reader = New-Object System.IO.StreamReader($stream)

    Write-Host "Reading stream events..." -ForegroundColor Green
    
    $eventCount = 0
    $hasSseStarted = $false
    
    while (!$reader.EndOfStream) {
        $line = $reader.ReadLine()
        if ($null -eq $line) { continue }
        
        $line = $line.Trim()
        if ($line.StartsWith("data:")) {
            $hasSseStarted = $true
            $data = $line.Substring(5).Trim()
            $eventCount++
            
            # Highlight important milestones in stream
            if ($data -match "workflow.started") {
                Write-Host "➜ Workflow Started" -ForegroundColor Blue
            } elseif ($data -match "agent.started") {
                Write-Host "➜ Agent Started" -ForegroundColor Yellow
            } elseif ($data -match "agent.responded") {
                Write-Host "➜ Agent Responded" -ForegroundColor DarkYellow
            } elseif ($data -match "decision.reached") {
                Write-Host "➜ Decision Reached" -ForegroundColor Cyan
            } elseif ($data -match "final.answer") {
                Write-Host "➜ Final Answer Received" -ForegroundColor Green
            } elseif ($data -match "stream.end") {
                Write-Host "➜ Stream End Marker Received" -ForegroundColor Green
            } else {
                # Print other events in gray
                # Limit length to keep output readable
                $snippet = if ($data.Length -gt 120) { $data.Substring(0, 120) + "..." } else { $data }
                Write-Host "  Event $eventCount: $snippet" -ForegroundColor Gray
            }
        }
    }
    
    $reader.Close()
    $stream.Close()
    
    if ($eventCount -gt 0) {
        Write-Host "`nSuccess: SSE stream verification completed successfully! Received $eventCount events." -ForegroundColor Green
    } else {
        Write-Host "`nFailure: Connection closed, but no SSE events (starting with 'data:') were received." -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "`nException during SSE stream request:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
finally {
    if ($null -ne $client) { $client.Dispose() }
}
