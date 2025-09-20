"""
Gemini-based Knowledge Agent for general knowledge and InfinitePay-specific queries.
"""
import os
import time

from bs4 import BeautifulSoup
import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory
import requests

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
        self._initialize_knowledge_base()

        logger.info("KnowledgeAgent initialized successfully")

    def _initialize_knowledge_base(self):
        """Initialize the InfinitePay knowledge base by scraping help content."""
        try:
            logger.info("Initializing KnowledgeAgent knowledge base")

            # Scrape InfinitePay help content
            help_url = "https://ajuda.infinitepay.io/pt-BR/"

            try:
                response = requests.get(help_url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract article links
                article_links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and '/articles/' in href:
                        full_url = href if href.startswith('http') else f"https://ajuda.infinitepay.io{href}"
                        article_links.append(full_url)

                logger.info(f"Found {len(article_links)} article links to scrape")

                # Scrape a subset of articles (limit to avoid overwhelming the system)
                scraped_content = []
                for i, url in enumerate(article_links[:10]):  # Limit to first 10 articles
                    try:
                        article_response = requests.get(url, timeout=5)
                        article_response.raise_for_status()

                        article_soup = BeautifulSoup(article_response.content, 'html.parser')

                        # Extract title and content
                        title = article_soup.find('h1')
                        title_text = title.get_text().strip() if title else "Unknown"

                        # Extract main content
                        content_div = article_soup.find('div', class_='article-body') or article_soup.find('main')
                        if content_div:
                            content_text = content_div.get_text().strip()
                            scraped_content.append({
                                'title': title_text,
                                'content': content_text[:1000],  # Limit content length
                                'url': url
                            })

                    except Exception as e:
                        logger.warning(f"Failed to scrape article {url}: {e}")
                        continue

                self.knowledge_base['infinitepay_articles'] = scraped_content
                logger.info(f"Successfully scraped {len(scraped_content)} articles")

            except Exception as e:
                logger.warning(f"Failed to scrape InfinitePay help: {e}")
                # Fallback knowledge base
                self.knowledge_base['infinitepay_articles'] = [
                    {
                        'title': 'InfinitePay Card Machine Fees',
                        'content': 'InfinitePay offers competitive card machine fees with transparent pricing.',
                        'url': help_url
                    }
                ]

        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")
            self.knowledge_base = {}

    def _get_relevant_context(self, message: str) -> str:
        """Get relevant context from the knowledge base."""
        context_parts = []

        # Check if query is about InfinitePay
        if any(keyword in message.lower() for keyword in ['infinitepay', 'payment', 'card', 'machine', 'fees']):
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
            if relevant_context:
                prompt = f"""You are a helpful assistant with expertise in InfinitePay payment solutions. Use the following context to answer the user's question:

CONTEXT:
{relevant_context}

USER QUESTION: {message}

Please provide a helpful, accurate response based on the context provided. If the question is about InfinitePay, use the context information. For general questions, provide helpful information while being concise and clear."""
            else:
                prompt = f"""You are a helpful assistant. Please answer the following question clearly and concisely:

{message}

Provide accurate, helpful information. If you're not certain about something, please say so."""

            # Generate response using Gemini
            response = self.model.generate_content(prompt)

            if not response.text:
                raise Exception("Empty response from Gemini API")

            execution_time = time.time() - start_time

            # Determine sources
            sources = []
            if relevant_context and any(keyword in message.lower() for keyword in ['infinitepay', 'payment', 'card']):
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
