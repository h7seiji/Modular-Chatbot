"""
MathAgent for processing mathematical expressions and calculations.
"""
import re
import time
import os
from typing import Any
from openai import OpenAI
from agents.base import SpecializedAgent
from models.core import ConversationContext, AgentResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MathAgent(SpecializedAgent):
    """Agent specialized in mathematical calculations using LLM interpretation."""
    
    def __init__(self):
        # Mathematical keywords for detection
        math_keywords = [
            "calculate", "compute", "solve", "math", "arithmetic", "equation",
            "add", "subtract", "multiply", "divide", "plus", "minus", "times",
            "divided", "sum", "difference", "product", "quotient", "equals",
            "what is", "how much", "result of", "answer to", "value of"
        ]
        super().__init__("MathAgent", math_keywords)
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.timeout = int(os.getenv("MATH_AGENT_TIMEOUT", "30"))
        
        # Mathematical expression patterns
        self.math_patterns = [
            r'\d+\s*[\+\-\*\/\^\%]\s*\d+',  # Basic arithmetic: 5 + 3, 10 * 2
            r'\d+\.\d+\s*[\+\-\*\/\^\%]\s*\d+\.?\d*',  # Decimals: 3.14 * 2
            r'\(\s*\d+\.?\d*\s*[\+\-\*\/\^\%]\s*\d+\.?\d*\s*\)',  # Parentheses: (5 + 3)
            r'\d+\.?\d*\s*[\+\-\*\/\^\%]\s*\(\s*\d+\.?\d*\s*[\+\-\*\/\^\%]\s*\d+\.?\d*\s*\)',  # Mixed
            r'sqrt\(\d+\.?\d*\)',  # Square root
            r'\d+\.?\d*\s*\^\s*\d+\.?\d*',  # Exponents
            r'sin\(\d+\.?\d*\)|cos\(\d+\.?\d*\)|tan\(\d+\.?\d*\)',  # Trigonometric
        ]
    
    def can_handle(self, message: str) -> float:
        """
        Determine if this agent can handle mathematical queries.
        
        Args:
            message: The input message to evaluate
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        message_lower = message.lower().strip()
        
        # High confidence for explicit mathematical expressions
        for pattern in self.math_patterns:
            if re.search(pattern, message_lower):
                logger.debug(f"Mathematical pattern detected: {pattern}")
                return 0.95
        
        # Medium-high confidence for mathematical keywords
        keyword_score = super().can_handle(message)
        if keyword_score > 0.3:
            return min(keyword_score + 0.4, 0.9)
        
        # Check for numbers and operators
        has_numbers = bool(re.search(r'\d+', message))
        has_operators = bool(re.search(r'[\+\-\*\/\=\^\%]', message))
        
        if has_numbers and has_operators:
            return 0.8
        elif has_numbers and any(word in message_lower for word in ["what", "how much", "calculate"]):
            return 0.7
        
        return keyword_score
    
    def _detect_mathematical_expressions(self, message: str) -> list[str]:
        """
        Extract mathematical expressions from the message.
        
        Args:
            message: Input message
            
        Returns:
            List of detected mathematical expressions
        """
        expressions = []
        
        for pattern in self.math_patterns:
            matches = re.findall(pattern, message)
            expressions.extend(matches)
        
        # Also look for simple number sequences with operators
        simple_math = re.findall(r'\d+\.?\d*\s*[\+\-\*\/\^\%]\s*\d+\.?\d*', message)
        expressions.extend(simple_math)
        
        return list(set(expressions))  # Remove duplicates
    
    def _validate_mathematical_input(self, expression: str) -> bool:
        """
        Validate that the mathematical input is safe to process.
        
        Args:
            expression: Mathematical expression to validate
            
        Returns:
            True if expression is safe, False otherwise
        """
        # Check for dangerous patterns
        dangerous_patterns = [
            r'import\s+',
            r'exec\s*\(',
            r'eval\s*\(',
            r'__\w+__',
            r'open\s*\(',
            r'file\s*\(',
            r'subprocess',
            r'os\.',
            r'sys\.',
        ]
        
        expression_lower = expression.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, expression_lower):
                logger.warning(f"Dangerous pattern detected in expression: {pattern}")
                return False
        
        # Check length to prevent abuse
        if len(expression) > 500:
            logger.warning(f"Expression too long: {len(expression)} characters")
            return False
        
        return True
    
    def _solve_with_llm(self, message: str, expressions: list[str]) -> str:
        """
        Use OpenAI LLM to solve mathematical expressions.
        
        Args:
            message: Original message
            expressions: Detected mathematical expressions
            
        Returns:
            LLM response with solution
        """
        # Create a focused prompt for mathematical calculation
        if expressions:
            expressions_text = ", ".join(expressions)
            prompt = f"""You are a mathematical calculator. Solve the following mathematical expression(s) accurately:

Expression(s): {expressions_text}

Original question: {message}

Please provide:
1. The step-by-step calculation
2. The final numerical answer
3. Keep your response concise and focused on the mathematics

Only perform mathematical calculations. Do not execute code or perform any other operations."""
        else:
            prompt = f"""You are a mathematical calculator. The user is asking a mathematical question:

Question: {message}

Please provide:
1. The step-by-step calculation if applicable
2. The final numerical answer
3. Keep your response concise and focused on the mathematics

Only perform mathematical calculations. Do not execute code or perform any other operations."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a precise mathematical calculator. Only perform mathematical calculations and provide numerical answers."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1,  # Low temperature for consistent mathematical results
                timeout=self.timeout
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise RuntimeError(f"Failed to process mathematical expression: {str(e)}")
    
    async def process(self, message: str, context: ConversationContext) -> AgentResponse:
        """
        Process a mathematical query and return the calculated result.
        
        Args:
            message: The mathematical query to process
            context: Conversation context
            
        Returns:
            AgentResponse containing the mathematical solution
        """
        start_time = time.time()
        
        logger.info(
            f"MathAgent processing query",
            extra={
                "conversation_id": context.conversation_id,
                "user_id": context.user_id,
                "message_length": len(message)
            }
        )
        
        try:
            # Detect mathematical expressions
            expressions = self._detect_mathematical_expressions(message)
            
            # Validate input safety
            if not self._validate_mathematical_input(message):
                raise ValueError("Invalid or unsafe mathematical input")
            
            # Solve using LLM
            solution = self._solve_with_llm(message, expressions)
            
            execution_time = time.time() - start_time
            
            # Log successful processing
            logger.info(
                f"MathAgent completed processing",
                extra={
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id,
                    "execution_time": execution_time,
                    "expressions_found": len(expressions),
                    "expressions": expressions
                }
            )
            
            return AgentResponse(
                content=solution,
                source_agent=self.name,
                execution_time=execution_time,
                metadata={
                    "expressions_detected": expressions,
                    "expression_count": len(expressions),
                    "model_used": "gpt-3.5-turbo",
                    "processing_method": "llm_interpretation"
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to process mathematical query: {str(e)}"
            
            logger.error(
                error_msg,
                extra={
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id,
                    "execution_time": execution_time,
                    "error": str(e)
                }
            )
            
            return AgentResponse(
                content="I apologize, but I encountered an error while processing your mathematical query. Please try rephrasing your question or check if the expression is valid.",
                source_agent=self.name,
                execution_time=execution_time,
                metadata={
                    "error": str(e),
                    "processing_failed": True
                }
            )