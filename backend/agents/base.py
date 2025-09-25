"""
Base agent interface and abstract classes for the modular chatbot system.
"""
from abc import ABC, abstractmethod
import re

from models.core import AgentDecision, AgentResponse, ConversationContext


class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""

    def __init__(self, name: str):
        """Initialize the agent with a name."""
        self.name = name

    @abstractmethod
    async def process(self, message: str, context: ConversationContext) -> AgentResponse:
        """
        Process a message and return a response.

        Args:
            message: The input message to process
            context: Conversation context including history

        Returns:
            AgentResponse containing the processed response
        """
        pass

    @abstractmethod
    def can_handle(self, message: str) -> float:
        """
        Determine if this agent can handle the given message.

        Args:
            message: The input message to evaluate

        Returns:
            Confidence score between 0.0 and 1.0
        """
        pass


class RouterAgent(BaseAgent):
    """Router agent responsible for directing messages to specialized agents."""

    def __init__(self):
        super().__init__("RouterAgent")
        self.agents: dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent) -> None:
        """Register a specialized agent with the router."""
        self.agents[agent.name] = agent

    async def route_message(self, message: str, context: ConversationContext) -> AgentDecision:
        """
        Route a message to the most appropriate agent.

        Args:
            message: The input message to route
            context: Conversation context

        Returns:
            AgentDecision containing routing information
        """
        # Get confidence scores from all agents
        scores = {}
        for agent_name, agent in self.agents.items():
            scores[agent_name] = agent.can_handle(message)

        # Select agent with highest confidence
        if not scores:
            raise ValueError("No agents registered")

        selected_agent = max(scores, key=scores.get) # type: ignore
        confidence = scores[selected_agent]
        alternatives = [name for name, score in scores.items()
                       if name != selected_agent and score > 0.1]

        return AgentDecision(
            selected_agent=selected_agent,
            confidence=confidence,
            reasoning=f"Selected {selected_agent} with confidence {confidence:.2f}",
            alternatives=alternatives
        )

    async def process(self, message: str, context: ConversationContext) -> AgentResponse:
        """
        Process a message by routing it to the appropriate agent.

        Args:
            message: The input message to process
            context: Conversation context

        Returns:
            AgentResponse from the selected agent
        """
        decision = await self.route_message(message, context)
        selected_agent = self.agents[decision.selected_agent]
        return await selected_agent.process(message, context)

    def can_handle(self, message: str) -> float:
        """Router can handle any message by delegating to other agents."""
        return 1.0


class SpecializedAgent(BaseAgent):
    """Base class for specialized agents (Math, Knowledge, etc.)."""

    def __init__(self, name: str, keywords: list[str] | None = None):
        super().__init__(name)
        self.keywords = keywords or []

    def can_handle(self, message: str) -> float:
        """
        Default implementation using keyword matching.
        Subclasses should override for more sophisticated logic.
        """
        if not self.keywords:
            return 0.0

        message_lower = message.lower()
        matches = sum(1 for keyword in self.keywords if keyword.lower() in message_lower)
        return min(matches / len(self.keywords), 1.0)


def math_score(message: str) -> float:
    """Return a confidence 0–1 that this is a math expression."""
    MATH_KEYWORDS = re.compile(r"(how much|calculate|result\s*of|solve|evaluate)", re.IGNORECASE)
    MATH_PHRASE_KEYWORD = re.compile(r"(what\s*is|what's)", re.IGNORECASE)
    MATH_PATTERN = re.compile(r"[\d]+(?:\s*[xX\*\+\-\/]\s*[\d]+)+")  # numbers with ops
    message = message.strip()

    has_ops = bool(MATH_PATTERN.search(message))
    has_keywords = bool(MATH_KEYWORDS.search(message) or MATH_PHRASE_KEYWORD.search(message))

    # scoring:
    if has_ops and has_keywords:
        return 1.0
    if has_ops:
        return 0.8
    if has_keywords and re.search(r"\d", message):  # keyword + at least one digit
        return 0.5
    return 0.0
