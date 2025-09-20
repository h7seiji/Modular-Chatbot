"""
Security middleware for the modular chatbot system.
Implements input sanitization, prompt injection detection, rate limiting, and secure error handling.
"""
import time
import json
from typing import Dict, Any, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.utils.validation import InputSanitizer, SecurityValidator
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class SecurityMiddleware:
    """Security middleware for input sanitization and threat detection."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip security checks for health endpoint
        if request.url.path == "/health":
            await self.app(scope, receive, send)
            return
        
        # Process request through security checks
        try:
            await self._process_request_security(request)
        except HTTPException as e:
            response = JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": "SECURITY_VIOLATION",
                        "message": e.detail,
                        "details": None
                    },
                    "request_id": str(id(request)),
                    "timestamp": time.time()
                }
            )
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send)
    
    async def _process_request_security(self, request: Request):
        """Process request through security validation."""
        # Log security check
        logger.info(
            "Processing security validation",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 1024 * 1024:  # 1MB limit
            logger.warning(
                "Request size too large",
                extra={
                    "content_length": content_length,
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request payload too large"
            )
        
        # For POST requests, validate JSON payload
        if request.method == "POST" and request.url.path == "/chat":
            await self._validate_chat_request(request)
    
    async def _validate_chat_request(self, request: Request):
        """Validate chat request payload for security threats."""
        try:
            # Get request body
            body = await request.body()
            if not body:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Empty request body"
                )
            
            # Parse JSON
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON format"
                )
            
            # Extract fields
            message = data.get("message", "")
            user_id = data.get("userId", "")
            conversation_id = data.get("conversationId", "")
            
            # Validate and sanitize input
            logger.info("Starting validation")
            is_valid, error_msg = SecurityValidator.validate_request_data(
                message, user_id, conversation_id
            )
            logger.info(f"Validation completed: {is_valid}")
            
            if not is_valid:
                logger.warning(
                    "Security validation failed",
                    extra={
                        "error": error_msg,
                        "client_ip": request.client.host if request.client else "unknown",
                        "user_id": self._mask_sensitive_data(user_id),
                        "message_length": len(message)
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            
            # Sanitize message content
            try:
                logger.info("Starting sanitization")
                sanitized_message = InputSanitizer.sanitize_input(message)
                logger.info("Sanitization completed")
                
                # Check if sanitization changed the content significantly
                if len(sanitized_message) < len(message) * 0.8:
                    logger.warning(
                        "Significant content removed during sanitization",
                        extra={
                            "original_length": len(message),
                            "sanitized_length": len(sanitized_message),
                            "client_ip": request.client.host if request.client else "unknown"
                        }
                    )
                
                # Update request data with sanitized content
                data["message"] = sanitized_message
                
                # Store sanitized data back in request scope for later use
                request.scope["sanitized_data"] = data
                
            except ValueError as e:
                logger.warning(
                    "Input sanitization failed",
                    extra={
                        "error": str(e),
                        "client_ip": request.client.host if request.client else "unknown"
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input content"
                )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during security validation",
                extra={
                    "error": str(e),
                    "client_ip": request.client.host if request.client else "unknown"
                },
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Security validation failed"
            )
    
    def _mask_sensitive_data(self, data: str) -> str:
        """Mask sensitive data for logging."""
        if not data or len(data) <= 4:
            return "***"
        return data[:2] + "*" * (len(data) - 4) + data[-2:]


class RequestLoggingMiddleware:
    """Middleware for comprehensive request/response logging with sensitive data masking."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        start_time = time.time()
        
        # Log request start
        await self._log_request_start(request)
        
        # Capture response
        response_body = b""
        response_status = 200
        
        async def send_wrapper(message):
            nonlocal response_body, response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
        
        # Log request completion
        process_time = time.time() - start_time
        await self._log_request_completion(request, response_status, response_body, process_time)
    
    async def _log_request_start(self, request: Request):
        """Log request start with masked sensitive data."""
        headers = dict(request.headers)
        
        # Mask sensitive headers
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "***MASKED***"
        
        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": headers.get("user-agent", "unknown"),
                "content_type": headers.get("content-type", "unknown"),
                "content_length": headers.get("content-length", "0")
            }
        )
    
    async def _log_request_completion(self, request: Request, status_code: int, 
                                    response_body: bytes, process_time: float):
        """Log request completion with response details."""
        # Parse response for logging (mask sensitive data)
        response_data = None
        if response_body:
            try:
                response_data = json.loads(response_body.decode())
                # Mask sensitive response data
                if isinstance(response_data, dict):
                    response_data = self._mask_response_data(response_data)
            except (json.JSONDecodeError, UnicodeDecodeError):
                response_data = {"size": len(response_body)}
        
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "process_time": process_time,
                "response_size": len(response_body),
                "response_data": response_data
            }
        )
    
    def _mask_response_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in response for logging."""
        masked_data = data.copy()
        
        # Mask potentially sensitive fields
        sensitive_fields = ["user_id", "conversation_id", "response"]
        for field in sensitive_fields:
            if field in masked_data and isinstance(masked_data[field], str):
                if field == "response":
                    # For response content, just log length and first few words
                    content = masked_data[field]
                    words = content.split()[:3]
                    masked_data[field] = f"{' '.join(words)}... (length: {len(content)})"
                else:
                    # For IDs, mask middle characters
                    value = masked_data[field]
                    if len(value) > 4:
                        masked_data[field] = value[:2] + "*" * (len(value) - 4) + value[-2:]
                    else:
                        masked_data[field] = "***"
        
        return masked_data


def setup_rate_limiting(app):
    """Set up rate limiting for the application."""
    # Add rate limiting middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    return limiter


# Rate limiting decorators for different endpoints
def rate_limit_chat():
    """Rate limit for chat endpoint: 30 requests per minute per IP."""
    return limiter.limit("30/minute")


def rate_limit_general():
    """Rate limit for general endpoints: 100 requests per minute per IP."""
    return limiter.limit("100/minute")