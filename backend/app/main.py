"""
FastAPI backend application for the modular chatbot system.
"""
from contextlib import asynccontextmanager
import time

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents.base import RouterAgent, SpecializedAgent
from agents.gemini_math_agent import MathAgent
from agents.knowledge_agent import KnowledgeAgent
from app.middleware.security import (
    RequestLoggingMiddleware,
    limiter,
    rate_limit_general,
    setup_rate_limiting,
)
from app.utils.logger import get_logger
from app.utils.validation import (
    InputSanitizer,
    SecurityValidator,
)
from models.core import ChatRequest, ChatResponse, ConversationContext, Message

# Initialize logger
logger = get_logger(__name__)

# Global router agent instance
router_agent: RouterAgent | None = None


class MockMathAgent(SpecializedAgent):
    """Mock Math Agent for testing purposes."""

    def __init__(self):
        super().__init__("MathAgent", keywords=["calculate", "math", "+", "-", "*", "/", "="])

    async def process(self, message: str, context: ConversationContext):
        """Process mathematical queries with mock responses."""
        from models.core import AgentResponse

        start_time = time.time()

        # Simple mock calculation logic
        if "+" in message:
            response_content = "I can help with addition! (This is a mock response)"
        elif "*" in message or "x" in message.lower():
            response_content = "I can help with multiplication! (This is a mock response)"
        elif "-" in message:
            response_content = "I can help with subtraction! (This is a mock response)"
        elif "/" in message:
            response_content = "I can help with division! (This is a mock response)"
        else:
            response_content = "I can help with mathematical calculations! (This is a mock response)"

        execution_time = time.time() - start_time

        logger.info(
            "MathAgent processed query",
            extra={
                "agent": "MathAgent",
                "conversation_id": context.conversation_id,
                "user_id": context.user_id,
                "execution_time": execution_time,
                "query_type": "mathematical"
            }
        )

        return AgentResponse(
            content=response_content,
            source_agent="MathAgent",
            execution_time=execution_time,
            metadata={"query_type": "mathematical", "mock": True}
        )


class MockKnowledgeAgent(SpecializedAgent):
    """Mock Knowledge Agent for testing purposes."""

    def __init__(self):
        super().__init__("KnowledgeAgent", keywords=["what", "how", "help", "infinitepay", "fees"])

    async def process(self, message: str, context: ConversationContext):
        """Process knowledge queries with mock responses."""
        from models.core import AgentResponse

        start_time = time.time()

        # Simple mock knowledge responses
        if "fees" in message.lower():
            response_content = "InfinitePay card machine fees vary by plan. (This is a mock response)"
        elif "infinitepay" in message.lower():
            response_content = "InfinitePay is a payment solution provider. (This is a mock response)"
        else:
            response_content = "I can help with InfinitePay information! (This is a mock response)"

        execution_time = time.time() - start_time

        logger.info(
            "KnowledgeAgent processed query",
            extra={
                "agent": "KnowledgeAgent",
                "conversation_id": context.conversation_id,
                "user_id": context.user_id,
                "execution_time": execution_time,
                "query_type": "knowledge"
            }
        )

        return AgentResponse(
            content=response_content,
            source_agent="KnowledgeAgent",
            execution_time=execution_time,
            metadata={"query_type": "knowledge", "mock": True},
            sources=["https://ajuda.infinitepay.io/pt-BR/ (mock)"]
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global router_agent

    # Startup
    logger.info("Starting up FastAPI application")

    # Initialize router agent and register agents
    router_agent = RouterAgent()

    # Try to initialize Gemini agents first, then fall back to OpenAI, then to mock
    try:
        math_agent = MathAgent()
        logger.info("MathAgent initialized successfully")
    except (ValueError, Exception) as e:
        logger.warning(f"Failed to initialize Gemini MathAgent: {e}, using mock")
        math_agent = MockMathAgent()

    # Try to initialize Gemini KnowledgeAgent first, then fall back to OpenAI, then to mock
    try:
        knowledge_agent = KnowledgeAgent()
        logger.info("KnowledgeAgent initialized successfully")
    except (ValueError, Exception) as e:
        logger.warning(f"Failed to initialize Gemini KnowledgeAgent: {e}, using mock")
        knowledge_agent = MockKnowledgeAgent()

    router_agent.register_agent(math_agent)
    router_agent.register_agent(knowledge_agent)

    logger.info("Router agent initialized with agents")

    yield

    # Shutdown
    logger.info("Shutting down FastAPI application")


# Create FastAPI application
app = FastAPI(
    title="Modular Chatbot API",
    description="A modular chatbot system with RouterAgent and specialized AI agents",
    version="0.1.0",
    lifespan=lifespan
)

# Set up rate limiting
limiter = setup_rate_limiting(app)

# Add security middleware (order matters - security first)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://frontend:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to prevent exposing internal details."""
    # Generate a unique request ID for tracking
    request_id = f"req_{int(time.time() * 1000)}_{id(request) % 10000}"

    # Log the full error details for internal debugging
    logger.error(
        f"Unhandled exception [Request ID: {request_id}]",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        },
        exc_info=True
    )

    # Return generic error response without internal details
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred. Please try again later.",
                "details": None
            },
            "request_id": request_id,
            "timestamp": time.time()
        }
    )


@app.get("/health")
@rate_limit_general()
async def health_check(request: Request):
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "0.1.0",
        "agents_registered": len(router_agent.agents) if router_agent else 0
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, http_request: Request) -> ChatResponse:
    """
    Main chat endpoint that processes user messages through the RouterAgent.
    
    Args:
        request: ChatRequest containing message, user_id, and conversation_id
        
    Returns:
        ChatResponse with agent response and workflow information
        
    Raises:
        HTTPException: For validation errors or processing failures
    """
    start_time = time.time()

    # Manual rate limiting
    try:

        # Check rate limit manually
        client_ip = http_request.client.host if http_request.client else "unknown"
        rate_limit_key = f"chat:{client_ip}"

        # Simple in-memory rate limiting (30 requests per minute)
        current_time = int(time.time() / 60)  # Current minute

        # This is a simplified rate limiting - in production, use Redis
        if not hasattr(app.state, 'rate_limits'):
            app.state.rate_limits = {}

        if rate_limit_key not in app.state.rate_limits:
            app.state.rate_limits[rate_limit_key] = {}

        minute_requests = app.state.rate_limits[rate_limit_key].get(current_time, 0)
        if minute_requests >= 30:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )

        # Increment counter
        app.state.rate_limits[rate_limit_key][current_time] = minute_requests + 1

        # Clean old entries (keep only last 2 minutes)
        for key in list(app.state.rate_limits[rate_limit_key].keys()):
            if key < current_time - 1:
                del app.state.rate_limits[rate_limit_key][key]

    except Exception as e:
        # If rate limiting fails, log but don't block the request
        logger.warning(f"Rate limiting error: {e}")

    try:
        # Use sanitized data from security middleware if available
        sanitized_data = getattr(http_request.scope, 'sanitized_data', None)
        if sanitized_data:
            # Use sanitized message content
            message_content = sanitized_data["message"]
            user_id = sanitized_data["user_id"]
            conversation_id = sanitized_data["conversation_id"]
        else:
            # Fallback to original request data with basic validation
            message_content = request.message
            user_id = request.user_id
            conversation_id = request.conversation_id

            # Comprehensive security validation
            is_valid, error_msg = SecurityValidator.validate_request_data(
                message_content, user_id, conversation_id
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )

            # Advanced sanitization and prompt injection detection
            if InputSanitizer.detect_prompt_injection(message_content):
                logger.warning(
                    "Prompt injection attempt detected",
                    extra={
                        "user_id": user_id[:8] + "***" if len(user_id) > 8 else "***",
                        "message_length": len(message_content),
                        "client_ip": http_request.client.host if http_request.client else "unknown"
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Potentially malicious content detected"
                )

            # Sanitize input
            message_content = InputSanitizer.sanitize_input(message_content)

        # Check if router agent is available
        if not router_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Router agent not available"
            )

        # Create conversation context with sanitized data
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            message_history=[
                Message(
                    content=message_content,
                    sender="user"
                )
            ]
        )

        # Log incoming request (with masked sensitive data)
        logger.info(
            "Processing chat request",
            extra={
                "agent": "RouterAgent",
                "conversation_id": conversation_id[:8] + "***" if len(conversation_id) > 8 else "***",
                "user_id": user_id[:4] + "***" if len(user_id) > 4 else "***",
                "message_length": len(message_content),
                "sanitized": sanitized_data is not None
            }
        )

        # Route message and get decision
        decision = await router_agent.route_message(message_content, context)

        # Process message with selected agent
        agent_response = await router_agent.process(message_content, context)

        # Calculate total processing time
        total_time = time.time() - start_time

        # Log routing decision (with masked sensitive data)
        logger.info(
            "Message routed successfully",
            extra={
                "agent": "RouterAgent",
                "level": "INFO",
                "conversation_id": conversation_id[:8] + "***" if len(conversation_id) > 8 else "***",
                "user_id": user_id[:4] + "***" if len(user_id) > 4 else "***",
                "decision": decision.selected_agent,
                "confidence": decision.confidence,
                "execution_time": total_time
            }
        )

        # Build response
        response = ChatResponse(
            response=agent_response.content,
            source_agent_response=f"{agent_response.source_agent} (confidence: {decision.confidence:.2f})",
            agent_workflow=[
                {
                    "agent": "RouterAgent",
                    "decision": f"Routed to {decision.selected_agent} with {decision.confidence:.2f} confidence"
                },
                {
                    "agent": decision.selected_agent,
                    "decision": f"Processed query in {agent_response.execution_time:.3f}s"
                }
            ]
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors (with masked sensitive data)
        logger.error(
            f"Error processing chat request: {e!s}",
            extra={
                "conversation_id": getattr(request, 'conversation_id', 'unknown')[:8] + "***",
                "user_id": getattr(request, 'user_id', 'unknown')[:4] + "***",
                "exception_type": type(e).__name__
            },
            exc_info=True
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        ) from e
