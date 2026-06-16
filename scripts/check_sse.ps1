param (
    [string]$BaseUrl = "http://localhost:8000",
    [string]$AuthToken = "",
    [string]$Message = "Verify SSE connectivity and agent responses"
)

# Load System.Net.Http assembly for HttpClient and StringContent
Add-Type -AssemblyName System.Net.Http

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

$targetUrl = "${BaseUrl}/api/chat/stream"
Write-Host ("Initiating streaming test at: {0}" -f $targetUrl) -ForegroundColor Cyan
Write-Host ("Message: {0}" -f $Message) -ForegroundColor Cyan

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
    # Construct HttpRequestMessage to use ResponseHeadersRead (prevents buffering)
    $request = New-Object System.Net.Http.HttpRequestMessage
    $request.Method = [System.Net.Http.HttpMethod]::Post
    $request.RequestUri = New-Object System.Uri($targetUrl)
    $request.Content = $content

    # Send request and return as soon as headers are read
    $responseTask = $client.SendAsync($request, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead)
    $response = $responseTask.GetAwaiter().GetResult()

    Write-Host ("Response Status Code: {0} ({1})" -f $response.StatusCode, [int]$response.StatusCode) -ForegroundColor Gray
    
    if (!$response.IsSuccessStatusCode) {
        $errorBody = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        Write-Host "Error: Stream failed to start!" -ForegroundColor Red
        Write-Host ("Details: {0}" -f $errorBody) -ForegroundColor Red
        exit 1
    }

    $contentType = $response.Content.Headers.ContentType.ToString()
    Write-Host ("Content-Type: {0}" -f $contentType) -ForegroundColor Gray
    
    if ($contentType -notmatch "text/event-stream") {
        Write-Host "Warning: Response is not text/event-stream! Might be buffered." -ForegroundColor Yellow
    }

    $stream = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
    
    Write-Host "Reading stream events..." -ForegroundColor Green
    
    $eventCount = 0
    $hasSseStarted = $false
    
    $buffer = New-Object byte[] 4096
    $stringBuffer = ""
    
    while ($true) {
        # Read from stream synchronously (blocking)
        try {
            $bytesRead = $stream.Read($buffer, 0, $buffer.Length)
        } catch {
            Write-Host ("Stream read error: {0}" -f $_.Exception.Message) -ForegroundColor Red
            break
        }
        
        if ($bytesRead -eq 0) {
            break # EOF
        }
        
        # Decode chunk and normalize line endings
        $chunk = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $bytesRead)
        $stringBuffer += $chunk
        $stringBuffer = $stringBuffer -replace "`r`n", "`n"
        
        # Process complete lines
        while ($stringBuffer.Contains("`n")) {
            $pos = $stringBuffer.IndexOf("`n")
            $line = $stringBuffer.Substring(0, $pos)
            $stringBuffer = $stringBuffer.Substring($pos + 1)
            
            $line = $line.Trim()
            if ([string]::IsNullOrEmpty($line)) {
                continue
            }
            
            # Skip heartbeats or keepalive comments
            if ($line.StartsWith(":")) {
                continue
            }
            
            if ($line.StartsWith("data:")) {
                $hasSseStarted = $true
                $data = $line.Substring(5).Trim()
                
                # Safeguard: replace empty data
                if ([string]::IsNullOrEmpty($data)) {
                    $data = "<empty>"
                }
                
                $eventCount++
                
                # Defensive check inside event parsing
                try {
                    $eventObj = $null
                    try {
                        $eventObj = $data | ConvertFrom-Json -ErrorAction Stop
                    } catch {
                        # JSON parsing failed, but we continue gracefully
                    }
                    
                    $eventType = ""
                    $msgText = ""
                    
                    if ($null -ne $eventObj) {
                        # Extract event type
                        if ($eventObj.PSObject.Properties['type']) {
                            $eventType = $eventObj.type
                        } elseif ($eventObj.PSObject.Properties['event']) {
                            $eventType = $eventObj.event
                        }
                        
                        # Extract message/details
                        if ($eventObj.PSObject.Properties['message']) {
                            $msgText = $eventObj.message
                        } elseif ($eventObj.PSObject.Properties['detail']) {
                            $msgText = $eventObj.detail
                        } elseif ($eventObj.PSObject.Properties['answer']) {
                            $ans = $eventObj.answer
                            if ($ans.Length -gt 60) { $ans = $ans.Substring(0, 60) + "..." }
                            $msgText = "Final Answer: $ans"
                        } elseif ($eventObj.PSObject.Properties['decision']) {
                            $msgText = "Decision: $($eventObj.decision)"
                        }
                    }
                    
                    # Regex fallback if JSON parsing or extraction didn't yield a type
                    if ([string]::IsNullOrEmpty($eventType)) {
                        if ($data -match "workflow.started") { $eventType = "workflow.started" }
                        elseif ($data -match "agent.started") { $eventType = "agent.started" }
                        elseif ($data -match "agent.responded") { $eventType = "agent.responded" }
                        elseif ($data -match "decision.reached") { $eventType = "decision.reached" }
                        elseif ($data -match "final.answer") { $eventType = "final.answer" }
                        elseif ($data -match "stream.end") { $eventType = "stream.end" }
                        else { $eventType = "generic.event" }
                    }
                    
                    # Structured status logs
                    $color = "Gray"
                    $prefix = "Event received"
                    
                    switch ($eventType) {
                        "workflow.started" {
                            $color = "Blue"
                            $prefix = "Workflow started"
                        }
                        "agent.started" {
                            $color = "Yellow"
                            $prefix = "Agent started"
                        }
                        "agent.responded" {
                            $color = "DarkYellow"
                            $prefix = "Agent responded"
                        }
                        "decision.reached" {
                            $color = "Cyan"
                            $prefix = "Decision reached"
                        }
                        "final.answer" {
                            $color = "Green"
                            $prefix = "Final answer received"
                        }
                        "stream.end" {
                            $color = "Green"
                            $prefix = "Stream end marker received"
                        }
                        "error" {
                            $color = "Red"
                            $prefix = "Error event"
                        }
                        default {
                            $color = "Gray"
                            $prefix = "Event received"
                        }
                    }
                    
                    # Truncate raw payload for summary
                    $snippet = $data
                    if ($snippet.Length -gt 120) {
                        $snippet = $snippet.Substring(0, 120) + "..."
                    }
                    if ([string]::IsNullOrEmpty($snippet)) {
                        $snippet = "<empty>"
                    }
                    
                    # Log to stdout using structured format
                    $description = $prefix
                    if (![string]::IsNullOrEmpty($msgText)) {
                        $description = "{0} ({1})" -f $prefix, $msgText
                    }
                    
                    Write-Host ("[Event {0}] {1} - {2}" -f ${eventCount}, ${description}, ${snippet}) -ForegroundColor $color
                    
                } catch {
                    $errText = $_.Exception.Message
                    Write-Warning ("Failed to parse event data for event {0}: {1}. Raw data: {2}" -f ${eventCount}, ${errText}, ${data})
                }
            }
        }
    }
    
    $stream.Close()
    
    if ($eventCount -gt 0) {
        Write-Host ("`nSuccess: SSE stream verification completed successfully! Received {0} events." -f ${eventCount}) -ForegroundColor Green
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
