"""
KnowledgeAgent for processing knowledge-based queries using RAG with InfinitePay help content.
"""
import os
import time
import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma
except ImportError:
    # Fallback to older import paths
    from langchain.embeddings.openai import OpenAIEmbeddings
    from langchain.vectorstores.chroma import Chroma
from langchain.schema import Document
from openai import OpenAI

from agents.base import SpecializedAgent
from models.core import ConversationContext, AgentResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeAgent(SpecializedAgent):
    """Agent specialized in knowledge-based queries using RAG with InfinitePay content."""
    
    def __init__(self):
        # Knowledge-related keywords for detection
        knowledge_keywords = [
            "what", "how", "why", "when", "where", "explain", "tell me",
            "information", "help", "support", "guide", "tutorial", "documentation",
            "infinitepay", "payment", "card", "machine", "fee", "rate", "service",
            "account", "transaction", "billing", "pricing", "plan", "feature",
            "setup", "configuration", "integration", "api", "webhook", "pix"
        ]
        super().__init__("KnowledgeAgent", knowledge_keywords)
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.timeout = int(os.getenv("KNOWLEDGE_AGENT_TIMEOUT", "30"))
        
        # RAG components
        self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # ChromaDB setup
        self.chroma_client = None
        self.vectorstore = None
        self.knowledge_base_url = "https://ajuda.infinitepay.io/pt-BR/"
        self.scraped_content = []
        
        # Initialize knowledge base
        asyncio.create_task(self._initialize_knowledge_base())
    
    def can_handle(self, message: str) -> float:
        """
        Determine if this agent can handle knowledge-based queries.
        
        Args:
            message: The input message to evaluate
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        message_lower = message.lower().strip()
        
        # High confidence for InfinitePay-specific terms
        infinitepay_terms = [
            "infinitepay", "infinite pay", "card machine", "payment processor",
            "maquininha", "taxa", "tarifa", "pix", "cartão"
        ]
        
        for term in infinitepay_terms:
            if term in message_lower:
                logger.debug(f"InfinitePay-specific term detected: {term}")
                return 0.95
        
        # Medium-high confidence for general knowledge keywords
        keyword_score = super().can_handle(message)
        if keyword_score > 0.2:
            return min(keyword_score + 0.3, 0.9)
        
        # Check for question patterns
        question_patterns = ["what", "how", "why", "when", "where", "can you", "do you know"]
        if any(pattern in message_lower for pattern in question_patterns):
            return 0.7
        
        # Check for help-seeking language
        help_patterns = ["help", "explain", "tell me", "information about", "guide"]
        if any(pattern in message_lower for pattern in help_patterns):
            return 0.6
        
        return keyword_score
    
    async def _initialize_knowledge_base(self) -> None:
        """Initialize the knowledge base by scraping InfinitePay help content."""
        try:
            logger.info("Initializing KnowledgeAgent knowledge base")
            
            # Set up ChromaDB
            chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
            self.chroma_client = chromadb.PersistentClient(
                path=chroma_persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Check if knowledge base already exists
            try:
                collection = self.chroma_client.get_collection("infinitepay_knowledge")
                if collection.count() > 0:
                    logger.info("Existing knowledge base found, loading...")
                    self.vectorstore = Chroma(
                        client=self.chroma_client,
                        collection_name="infinitepay_knowledge",
                        embedding_function=self.embeddings
                    )
                    return
            except Exception:
                logger.info("No existing knowledge base found, creating new one...")
            
            # Scrape content from InfinitePay help site
            await self._scrape_infinitepay_content()
            
            # Create vector store
            if self.scraped_content:
                documents = self._create_documents_from_content()
                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    client=self.chroma_client,
                    collection_name="infinitepay_knowledge"
                )
                logger.info(f"Knowledge base initialized with {len(documents)} documents")
            else:
                logger.warning("No content scraped, knowledge base will be empty")
                
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {str(e)}")
            # Create empty vectorstore as fallback
            self.vectorstore = Chroma(
                embedding_function=self.embeddings,
                client=self.chroma_client,
                collection_name="infinitepay_knowledge"
            )
    
    async def _scrape_infinitepay_content(self) -> None:
        """Scrape content from InfinitePay help website."""
        try:
            logger.info(f"Starting to scrape content from {self.knowledge_base_url}")
            
            # Get the main help page
            response = requests.get(self.knowledge_base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all article links
            article_links = set()
            
            # Look for common link patterns in help sites
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/') or self.knowledge_base_url in href:
                    full_url = urljoin(self.knowledge_base_url, href)
                    if self._is_valid_help_url(full_url):
                        article_links.add(full_url)
            
            # Also scrape the main page content
            main_content = self._extract_content_from_page(soup, self.knowledge_base_url)
            if main_content:
                self.scraped_content.append(main_content)
            
            # Limit the number of pages to scrape to avoid overwhelming the server
            max_pages = int(os.getenv("MAX_SCRAPE_PAGES", "50"))
            article_links = list(article_links)[:max_pages]
            
            logger.info(f"Found {len(article_links)} article links to scrape")
            
            # Scrape individual articles
            for url in article_links:
                try:
                    await asyncio.sleep(1)  # Be respectful to the server
                    article_response = requests.get(url, timeout=15)
                    article_response.raise_for_status()
                    
                    article_soup = BeautifulSoup(article_response.content, 'html.parser')
                    content = self._extract_content_from_page(article_soup, url)
                    
                    if content:
                        self.scraped_content.append(content)
                        logger.debug(f"Scraped content from {url}")
                    
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {str(e)}")
                    continue
            
            logger.info(f"Successfully scraped {len(self.scraped_content)} pages")
            
        except Exception as e:
            logger.error(f"Failed to scrape InfinitePay content: {str(e)}")
            # Add some fallback content
            self.scraped_content = [{
                'title': 'InfinitePay Help',
                'content': 'InfinitePay is a payment processing service that provides card machines and payment solutions.',
                'url': self.knowledge_base_url
            }]
    
    def _is_valid_help_url(self, url: str) -> bool:
        """Check if URL is a valid help article URL."""
        parsed = urlparse(url)
        
        # Skip non-help URLs
        skip_patterns = [
            'javascript:', 'mailto:', 'tel:', '#',
            '.pdf', '.jpg', '.png', '.gif', '.css', '.js',
            'login', 'signup', 'register', 'download'
        ]
        
        for pattern in skip_patterns:
            if pattern in url.lower():
                return False
        
        # Only include URLs from the help domain
        return 'ajuda.infinitepay.io' in parsed.netloc
    
    def _extract_content_from_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, str]]:
        """Extract meaningful content from a webpage."""
        try:
            # Try to find the main content area
            content_selectors = [
                'article', 'main', '.content', '.article-content',
                '.help-content', '.documentation', '.guide'
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
            
            if not content_element:
                content_element = soup.find('body')
            
            if not content_element:
                return None
            
            # Extract title
            title = ""
            title_element = soup.find('title')
            if title_element:
                title = title_element.get_text().strip()
            
            if not title:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text().strip()
            
            # Extract text content
            # Remove script and style elements
            for script in content_element(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            text = content_element.get_text()
            
            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            if len(text) < 50:  # Skip very short content
                return None
            
            return {
                'title': title,
                'content': text,
                'url': url
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {str(e)}")
            return None
    
    def _create_documents_from_content(self) -> List[Document]:
        """Create LangChain documents from scraped content."""
        documents = []
        
        for content_item in self.scraped_content:
            # Split content into chunks
            text_chunks = self.text_splitter.split_text(content_item['content'])
            
            for i, chunk in enumerate(text_chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        'title': content_item['title'],
                        'url': content_item['url'],
                        'chunk_index': i,
                        'source': 'infinitepay_help'
                    }
                )
                documents.append(doc)
        
        return documents
    
    def _retrieve_relevant_content(self, query: str, k: int = 5) -> List[Document]:
        """Retrieve relevant documents for the query."""
        if not self.vectorstore:
            logger.warning("Vector store not initialized")
            return []
        
        try:
            # Perform similarity search
            docs = self.vectorstore.similarity_search(query, k=k)
            logger.debug(f"Retrieved {len(docs)} relevant documents for query")
            return docs
        except Exception as e:
            logger.error(f"Failed to retrieve relevant content: {str(e)}")
            return []
    
    def _generate_response_with_context(self, query: str, context_docs: List[Document]) -> str:
        """Generate response using retrieved context and LLM."""
        if not context_docs:
            return "I apologize, but I don't have specific information about that topic in my knowledge base. Could you please rephrase your question or ask about InfinitePay services?"
        
        # Prepare context from retrieved documents
        context_text = ""
        sources = []
        
        for doc in context_docs:
            context_text += f"Source: {doc.metadata.get('title', 'Unknown')}\n"
            context_text += f"Content: {doc.page_content}\n\n"
            
            source_url = doc.metadata.get('url', '')
            if source_url and source_url not in sources:
                sources.append(source_url)
        
        # Create prompt for LLM
        prompt = f"""You are a helpful assistant for InfinitePay, a payment processing service. Use the following context information to answer the user's question accurately and helpfully.

Context Information:
{context_text}

User Question: {query}

Instructions:
1. Answer based primarily on the provided context
2. Be helpful and informative
3. If the context doesn't fully answer the question, say so
4. Keep your response concise but complete
5. Focus on InfinitePay-specific information when available

Answer:"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable assistant for InfinitePay payment services. Provide accurate, helpful information based on the context provided."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3,
                timeout=self.timeout
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return "I apologize, but I encountered an error while processing your question. Please try again later."
    
    async def process(self, message: str, context: ConversationContext) -> AgentResponse:
        """
        Process a knowledge-based query using RAG.
        
        Args:
            message: The knowledge query to process
            context: Conversation context
            
        Returns:
            AgentResponse containing the knowledge-based response
        """
        start_time = time.time()
        
        logger.info(
            f"KnowledgeAgent processing query",
            extra={
                "conversation_id": context.conversation_id,
                "user_id": context.user_id,
                "message_length": len(message)
            }
        )
        
        try:
            # Ensure knowledge base is initialized
            if not self.vectorstore:
                await self._initialize_knowledge_base()
            
            # Retrieve relevant documents
            relevant_docs = self._retrieve_relevant_content(message)
            
            # Generate response with context
            response_content = self._generate_response_with_context(message, relevant_docs)
            
            # Extract sources
            sources = []
            for doc in relevant_docs:
                source_url = doc.metadata.get('url', '')
                if source_url and source_url not in sources:
                    sources.append(source_url)
            
            execution_time = time.time() - start_time
            
            # Log successful processing
            logger.info(
                f"KnowledgeAgent completed processing",
                extra={
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id,
                    "execution_time": execution_time,
                    "documents_retrieved": len(relevant_docs),
                    "sources_found": len(sources)
                }
            )
            
            return AgentResponse(
                content=response_content,
                source_agent=self.name,
                execution_time=execution_time,
                metadata={
                    "documents_retrieved": len(relevant_docs),
                    "model_used": "gpt-3.5-turbo",
                    "processing_method": "rag_retrieval",
                    "knowledge_base": "infinitepay_help"
                },
                sources=sources
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to process knowledge query: {str(e)}"
            
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
                content="I apologize, but I encountered an error while searching for information. Please try rephrasing your question or ask about InfinitePay services in a different way.",
                source_agent=self.name,
                execution_time=execution_time,
                metadata={
                    "error": str(e),
                    "processing_failed": True
                }
            )