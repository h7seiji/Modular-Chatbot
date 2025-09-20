# PowerShell script to test the FastAPI backend with Docker Compose

Write-Host "🚀 Testing FastAPI backend with Docker Compose..." -ForegroundColor Cyan

# Function to test endpoint
function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Url,
        [string]$Data,
        [string]$Description
    )
    
    Write-Host "`n🔍 Testing: $Description" -ForegroundColor Yellow
    Write-Host "URL: $Url"
    
    try {
        if ($Data) {
            Write-Host "Data: $Data"
            $response = Invoke-RestMethod -Uri $Url -Method $Method -Body $Data -ContentType "application/json" -ErrorAction Stop
        } else {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -ErrorAction Stop
        }
        
        Write-Host "✅ Success" -ForegroundColor Green
        Write-Host "Response: $($response | ConvertTo-Json -Depth 3)"
        return $true
    }
    catch {
        Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)"
        }
        return $false
    }
}

# Function to test endpoint expecting failure
function Test-EndpointExpectFailure {
    param(
        [string]$Method,
        [string]$Url,
        [string]$Data,
        [string]$Description,
        [int]$ExpectedStatusCode = 400
    )
    
    Write-Host "`n🔍 Testing: $Description (should fail)" -ForegroundColor Yellow
    Write-Host "URL: $Url"
    
    try {
        if ($Data) {
            Write-Host "Data: $Data"
            $response = Invoke-RestMethod -Uri $Url -Method $Method -Body $Data -ContentType "application/json" -ErrorAction Stop
        } else {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -ErrorAction Stop
        }
        
        Write-Host "❌ Test failed: Expected failure but got success" -ForegroundColor Red
        return $false
    }
    catch {
        if ($_.Exception.Response.StatusCode.value__ -eq $ExpectedStatusCode) {
            Write-Host "✅ Validation test passed (HTTP $($_.Exception.Response.StatusCode.value__))" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Wrong status code: Expected $ExpectedStatusCode, got $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
            return $false
        }
    }
}

# Wait for backend service to be ready
Write-Host "Waiting for backend service to be ready..."
$maxAttempts = 30
$attempt = 0

do {
    $attempt++
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✅ Backend service is ready!" -ForegroundColor Green
        break
    }
    catch {
        Write-Host "Waiting... ($attempt/$maxAttempts)"
        Start-Sleep -Seconds 2
    }
} while ($attempt -lt $maxAttempts)

if ($attempt -eq $maxAttempts) {
    Write-Host "❌ Backend service is not responding after $maxAttempts attempts" -ForegroundColor Red
    exit 1
}

# Test health endpoint
$success = Test-Endpoint -Method "GET" -Url "http://localhost:8000/health" -Description "Health check endpoint"

# Test chat endpoint with math query
$mathData = @{
    message = "What is 5 + 3?"
    user_id = "test_user_123"
    conversation_id = "test_conv_456"
} | ConvertTo-Json

$success = $success -and (Test-Endpoint -Method "POST" -Url "http://localhost:8000/chat" -Data $mathData -Description "Chat endpoint with math query")

# Test chat endpoint with knowledge query
$knowledgeData = @{
    message = "What are the InfinitePay card machine fees?"
    user_id = "test_user_789"
    conversation_id = "test_conv_101"
} | ConvertTo-Json

$success = $success -and (Test-Endpoint -Method "POST" -Url "http://localhost:8000/chat" -Data $knowledgeData -Description "Chat endpoint with knowledge query")

# Test input validation (empty message)
$invalidData = @{
    message = ""
    user_id = "test_user"
    conversation_id = "test_conv"
} | ConvertTo-Json

$success = $success -and (Test-EndpointExpectFailure -Method "POST" -Url "http://localhost:8000/chat" -Data $invalidData -Description "Input validation with empty message" -ExpectedStatusCode 400)

# Test input validation (invalid user_id)
$invalidUserData = @{
    message = "Hello"
    user_id = "invalid@user"
    conversation_id = "test_conv"
} | ConvertTo-Json

$success = $success -and (Test-EndpointExpectFailure -Method "POST" -Url "http://localhost:8000/chat" -Data $invalidUserData -Description "Input validation with invalid user_id" -ExpectedStatusCode 400)

if ($success) {
    Write-Host "`n🎉 All API tests passed successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n❌ Some tests failed" -ForegroundColor Red
    exit 1
}