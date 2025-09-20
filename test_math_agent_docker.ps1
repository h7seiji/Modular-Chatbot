# PowerShell script for testing MathAgent in Docker environment
Write-Host "🧮 Testing MathAgent in Docker Environment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "🐳 Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Build and start the services
Write-Host "🔨 Building and starting services..." -ForegroundColor Yellow
docker-compose -f docker-compose.yml up -d --build

# Wait for services to be ready
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test health endpoint
Write-Host "🏥 Testing health endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "✅ Health endpoint accessible" -ForegroundColor Green
    Write-Host "   Response: $($healthResponse | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Health endpoint not accessible: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "🧮 Testing mathematical queries..." -ForegroundColor Cyan

# Test 1: Simple addition
Write-Host "📝 Test 1: Simple addition" -ForegroundColor Yellow
try {
    $body1 = @{
        message = "What is 5 + 3?"
        user_id = "test_user_1"
        conversation_id = "test_conv_1"
    } | ConvertTo-Json

    $response1 = Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -Body $body1 -ContentType "application/json"
    Write-Host "✅ Addition query successful" -ForegroundColor Green
    Write-Host "   Response: $($response1 | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Addition query failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Multiplication
Write-Host ""
Write-Host "📝 Test 2: Multiplication" -ForegroundColor Yellow
try {
    $body2 = @{
        message = "How much is 65 x 3.11?"
        user_id = "test_user_2"
        conversation_id = "test_conv_2"
    } | ConvertTo-Json

    $response2 = Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -Body $body2 -ContentType "application/json"
    Write-Host "✅ Multiplication query successful" -ForegroundColor Green
    Write-Host "   Response: $($response2 | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Multiplication query failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Complex expression
Write-Host ""
Write-Host "📝 Test 3: Complex expression" -ForegroundColor Yellow
try {
    $body3 = @{
        message = "Calculate (42 * 2) / 6"
        user_id = "test_user_3"
        conversation_id = "test_conv_3"
    } | ConvertTo-Json

    $response3 = Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -Body $body3 -ContentType "application/json"
    Write-Host "✅ Complex expression query successful" -ForegroundColor Green
    Write-Host "   Response: $($response3 | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Complex expression query failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Non-mathematical query (should not go to MathAgent)
Write-Host ""
Write-Host "📝 Test 4: Non-mathematical query" -ForegroundColor Yellow
try {
    $body4 = @{
        message = "What are InfinitePay fees?"
        user_id = "test_user_4"
        conversation_id = "test_conv_4"
    } | ConvertTo-Json

    $response4 = Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -Body $body4 -ContentType "application/json"
    Write-Host "✅ Non-mathematical query successful" -ForegroundColor Green
    Write-Host "   Response: $($response4 | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Non-mathematical query failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "📊 Docker testing completed!" -ForegroundColor Cyan
Write-Host "💡 Check the responses above to verify MathAgent is working correctly" -ForegroundColor Yellow
Write-Host ""
Write-Host "🛑 To stop the services, run: docker-compose down" -ForegroundColor Red