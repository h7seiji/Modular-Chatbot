"""
Gemini-based Knowledge Agent for general knowledge and InfinitePay-specific queries.
"""
import os
import time

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain.vectorstores import FAISS
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

from agents.base import SpecializedAgent
from app.utils.logger import get_logger
from models.core import AgentResponse, ConversationContext

logger = get_logger(__name__)


class KnowledgeAgent(SpecializedAgent):
    """Knowledge agent powered by Google Gemini with InfinitePay expertise."""

    def __init__(self):
        super().__init__("KnowledgeAgent", keywords=[
            "what", "how", "why", "when", "where", "who", "help", "explain",
            "infinitepay", "payment", "card", "machine", "fees", "support",
            "account", "transaction", "billing", "setup", "configure",
            "problem", "issue", "error", "troubleshoot", "guide", "tutorial"
        ])

        # Initialize Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=api_key)

        embeddings = VertexAIEmbeddings(model_name="text-embedding-004")
        vectorstore = FAISS.load_local("infinitepay_faiss_index", embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

        llm = ChatVertexAI(model_name="gemini-1.5-flash", temperature=0)

        # Prompt: how to inject docs into the LLM
        prompt = ChatPromptTemplate.from_template(
            "Use the following context to answer the question.\n\n{context}\n\nQuestion: {input}"
        )

        # Combine retrieved documents into one input string
        document_chain = create_stuff_documents_chain(llm, prompt)

        # Wrap it all into a retrieval chain
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        # Configure the model
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.3,  # Slightly higher for more natural responses
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 2048,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )

        # Initialize knowledge base
        self.knowledge_base = {}

        logger.info("KnowledgeAgent initialized successfully")

    def _get_relevant_context(self, message: str) -> str:
        """Get relevant context from the knowledge base."""
        context_parts = []

        # Check if query is about InfinitePay
        # if any(keyword in message.lower() for keyword in ['infinitepay', 'payment', 'card', 'machine', 'fees']):
        articles = self.knowledge_base.get('infinitepay_articles', [])
        for article in articles[:3]:  # Use top 3 relevant articles
            context_parts.append(f"Title: {article['title']}\nContent: {article['content']}\n")

        return "\n".join(context_parts) if context_parts else ""

    async def process(self, message: str, context: ConversationContext) -> AgentResponse:
        """Process knowledge queries using Gemini."""
        start_time = time.time()

        try:
            logger.info(
                "KnowledgeAgent processing query",
                extra={
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id,
                    "message_length": len(message)
                }
            )

            # Get relevant context from knowledge base
            relevant_context = self._get_relevant_context(message)

            # Create a comprehensive prompt
            prompt = f"""You are a helpful assistant with expertise in InfinitePay payment solutions. Use the following context to answer the user's question:

CONTEXT:
{relevant_context}

USER QUESTION: {message}

Please provide a helpful, accurate response based on the context provided. If the question is about InfinitePay, use the context information. For general questions, provide helpful information while being concise and clear."""

            # Generate response using Gemini
            response = self.model.generate_content(prompt)

            if not response.text:
                raise Exception("Empty response from Gemini API")

            execution_time = time.time() - start_time

            # Determine sources
            # sources = []
            # if relevant_context and any(keyword in message.lower() for keyword in ['infinitepay', 'payment', 'card']):
            sources = ["https://ajuda.infinitepay.io/pt-BR/"]

            logger.info(
                "KnowledgeAgent completed processing",
                extra={
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id,
                    "execution_time": execution_time,
                    "response_length": len(response.text),
                    "used_context": bool(relevant_context)
                }
            )

            return AgentResponse(
                content=response.text.strip(),
                source_agent="KnowledgeAgent",
                execution_time=execution_time,
                metadata={
                    "model": "gemini-1.5-flash",
                    "query_type": "knowledge",
                    "used_context": bool(relevant_context),
                    "temperature": 0.3
                },
                sources=sources
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
                content = "I'm currently experiencing high demand. Please try your question again in a moment."
            elif "safety" in error_msg.lower():
                content = "I can't process that request due to safety guidelines. Please rephrase your question."
            else:
                content = "I encountered an error while processing your question. Please try rephrasing it or ask something else."

            return AgentResponse(
                content=content,
                source_agent="KnowledgeAgent",
                execution_time=execution_time,
                metadata={
                    "error": True,
                    "error_type": type(e).__name__,
                    "model": "gemini-1.5-flash"
                }
            )
