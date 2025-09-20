"""
Core data models for the modular chatbot system.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a single message in a conversation."""
    content: str = Field(..., description="The message content")
    sender: str = Field(..., description="Message sender: 'user' or 'agent'")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    agent_type: Optional[str] = Field(None, description="Type of agent that generated this message")


class ConversationContext(BaseModel):
    """Context information for a conversation."""
    conversation_id: str = Field(..., description="Unique conversation identifier")
    user_id: str = Field(..., description="User identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Context creation timestamp")
    message_history: List[Message] = Field(default_factory=list, description="List of messages in conversation")


class AgentDecision(BaseModel):
    """Represents a routing decision made by the RouterAgent."""
    selected_agent: str = Field(..., description="Name of the selected agent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the decision")
    reasoning: str = Field(..., description="Explanation of why this agent was selected")
    alternatives: List[str] = Field(default_factory=list, description="Alternative agents considered")


class AgentResponse(BaseModel):
    """Response from a specialized agent."""
    content: str = Field(..., description="The response content")
    source_agent: str = Field(..., description="Name of the agent that generated this response")
    execution_time: float = Field(..., ge=0.0, description="Time taken to generate response in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    sources: Optional[List[str]] = Field(None, description="Sources used to generate the response")


class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""
    message: str = Field(..., description="User message")
    user_id: str = Field(..., alias="userId", description="User identifier")
    conversation_id: str = Field(..., alias="conversationId", description="Conversation identifier")


class ChatResponse(BaseModel):
    """Response model for the chat endpoint."""
    response: str = Field(..., description="Agent response")
    source_agent_response: str = Field(..., description="Source agent information")
    agent_workflow: List[Dict[str, str]] = Field(..., description="Workflow information")