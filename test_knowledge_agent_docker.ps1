#!/usr/bin/env pwsh
<#
.SYNOPSIS
Test script to verify KnowledgeAgent functionality in Docker environment.

.DESCRIPTION
This script tests the KnowledgeAgent by making HTTP requests to the Docker container.
#>

# Docker container URL
$baseUrl = "http://localhost:8000"

Write-Host "🚀 Testing KnowledgeAgent in Docker Environment" -ForegroundColor Green
Write-Host "=" * 50

# Test health endpoint first
Write-Host "Testing health endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get -TimeoutSec 10
    Write-Host "✅ Health check passed" -ForegroundColor Green
    Write-Host "   Status: $($healthResponse.status)"
    Write-Host "   Agents registered: $($healthResponse.agents_registered)"
}
catch {
    Write-Host "❌ Cannot connect to Docker container: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Make sure the Docker container is running on port 8000" -ForegroundColor Yellow
    exit 1
}

# Test knowledge queries
$knowledgeQueries = @(
    "What are InfinitePay card machine fees?",
    "How do I set up my InfinitePay account?",
    "Tell me about payment processing services",
    "What is PIX payment?",
    "How does InfinitePay work?"
)

Write-Host "`nTesting $($knowledgeQueries.Count) knowledge queries..." -ForegroundColor Yellow

for ($i = 0; $i -lt $knowledgeQueries.Count; $i++) {
    $query = $knowledgeQueries[$i]
    $queryNum = $i + 1
    
    Write-Host "`n$queryNum. Testing query: '$query'" -ForegroundColor Cyan
    
    # Prepare request
    $chatRequest = @{
        message = $query
        user_id = "test-user-123"
        conversation_id = "test-conv-$queryNum"
    }
    
    try {
        $startTime = Get-Date
        $response = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -Body ($chatRequest | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 30
        $responseTime = (Get-Date) - $startTime
        
        Write-Host "   ✅ Response received in $($responseTime.TotalSeconds.ToString('F2'))s" -ForegroundColor Green
        Write-Host "      Source agent: $($response.source_agent_response)"
        
        # Check if KnowledgeAgent was used
        $knowledgeAgentUsed = $response.agent_workflow | Where-Object { $_ -match "KnowledgeAgent" }
        
        if ($knowledgeAgentUsed) {
            Write-Host "      ✅ KnowledgeAgent was used" -ForegroundColor Green
        } else {
            Write-Host "      ⚠️  KnowledgeAgent was not used (routed to different agent)" -ForegroundColor Yellow
        }
        
        # Show response preview
        $responseContent = $response.response
        $preview = if ($responseContent.Length -gt 100) { $responseContent.Substring(0, 100) + "..." } else { $responseContent }
        Write-Host "      Response: $preview"
        
        # Show workflow
        Write-Host "      Workflow: $($response.agent_workflow | ConvertTo-Json -Compress)"
        
    }
    catch {
        if ($_.Exception.Message -match "timeout") {
            Write-Host "   ❌ Request timed out after 30 seconds" -ForegroundColor Red
        } else {
            Write-Host "   ❌ Request failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Test mathematical query (should NOT go to KnowledgeAgent)
$mathQueryNum = $knowledgeQueries.Count + 1
Write-Host "`n$mathQueryNum. Testing mathematical query (should go to MathAgent):" -ForegroundColor Cyan
$mathQuery = "What is 5 + 3?"
Write-Host "   Query: '$mathQuery'"

try {
    $mathRequest = @{
        message = $mathQuery
        user_id = "test-user-123"
        conversation_id = "test-conv-math"
    }
    
    $response = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -Body ($mathRequest | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 30
    
    $mathAgentUsed = $response.agent_workflow | Where-Object { $_ -match "MathAgent" }
    
    if ($mathAgentUsed) {
        Write-Host "   ✅ Correctly routed to MathAgent" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Not routed to MathAgent: $($response.agent_workflow | ConvertTo-Json -Compress)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ❌ Math query error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n$('=' * 50)"
Write-Host "🎉 KnowledgeAgent Docker Tests Completed" -ForegroundColor Green