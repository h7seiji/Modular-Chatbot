"""
Gemini-based Math Agent for mathematical calculations and problem solving.
"""
import os
import time

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory

from agents.base import SpecializedAgent
from app.utils.logger import get_logger
from models.core import AgentResponse, ConversationContext

logger = get_logger(__name__)


class MathAgent(SpecializedAgent):
    """Math agent powered by Google Gemini for mathematical calculations."""

    def __init__(self):
        super().__init__("MathAgent", keywords=[
            "calculate", "math", "mathematics", "equation", "solve", "compute",
            "+", "-", "*", "/", "=", "equals", "sum", "difference", "product",
            "quotient", "percentage", "percent", "square", "root", "power",
            "algebra", "geometry", "trigonometry", "calculus", "statistics"
        ])

        # Initialize Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=api_key)

        # Configure the model
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",  # Fast and efficient model
            generation_config={
                "temperature": 0.1,  # Low temperature for consistent math results
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )

        logger.info("MathAgent initialized successfully")

    async def process(self, message: str, context: ConversationContext) -> AgentResponse:
        """Process mathematical queries using Gemini."""
        start_time = time.time()

        try:
            logger.info(
                "MathAgent processing query",
                extra={
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id,
                    "message_length": len(message)
                }
            )

            # Create a focused math prompt
            prompt = f"""You are a helpful math assistant. Solve this mathematical problem step by step:

{message}

Please provide:
1. A clear step-by-step solution
2. The final answer
3. If it's a word problem, explain your reasoning

Be precise and show your work. If the question is not mathematical, politely redirect to math-related topics."""

            # Generate response using Gemini
            response = self.model.generate_content(prompt)

            if not response.text:
                raise Exception("Empty response from Gemini API")

            execution_time = time.time() - start_time

            logger.info(
                "MathAgent completed processing",
                extra={
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id,
                    "execution_time": execution_time,
                    "response_length": len(response.text)
                }
            )

            return AgentResponse(
                content=response.text.strip(),
                source_agent="MathAgent",
                execution_time=execution_time,
                metadata={
                    "model": "gemini-1.5-flash",
                    "query_type": "mathematical",
                    "temperature": 0.1
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            logger.error(
                f"Gemini API error: {error_msg}",
                extra={
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id,
                    "execution_time": execution_time,
                    "error_type": type(e).__name__
                }
            )

            # Provide a helpful error message
            if "quota" in error_msg.lower() or "limit" in error_msg.lower():
                content = "I'm currently experiencing high demand. Please try your math question again in a moment."
            elif "safety" in error_msg.lower():
                content = "I can't process that request due to safety guidelines. Please rephrase your math question."
            else:
                content = "I encountered an error while processing your mathematical query. Please try rephrasing your question or check if the expression is valid."

            return AgentResponse(
                content=content,
                source_agent="MathAgent",
                execution_time=execution_time,
                metadata={
                    "error": True,
                    "error_type": type(e).__name__,
                    "model": "gemini-1.5-flash"
                }
            )
