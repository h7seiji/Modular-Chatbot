"""
Unit tests for KnowledgeAgent.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import os

from backend.agents.knowledge_agent import KnowledgeAgent
from backend.models.core import ConversationContext, Message, AgentResponse


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch('backend.agents.knowledge_agent.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test response from the knowledge agent."
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_embeddings():
    """Mock OpenAI embeddings."""
    with patch('backend.agents.knowledge_agent.OpenAIEmbeddings') as mock_emb:
        yield mock_emb.return_value


@pytest.fixture
def mock_chroma():
    """Mock ChromaDB components."""
    with patch('backend.agents.knowledge_agent.chromadb') as mock_chromadb, \
         patch('backend.agents.knowledge_agent.Chroma') as mock_chroma_class:
        
        # Mock persistent client
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.count.return_value = 0
        mock_client.get_collection.side_effect = Exception("Collection not found")
        mock_chromadb.PersistentClient.return_value = mock_client
        
        # Mock Chroma vectorstore
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search.return_value = []
        mock_chroma_class.return_value = mock_vectorstore
        mock_chroma_class.from_documents.return_value = mock_vectorstore
        
        yield {
            'client': mock_client,
            'vectorstore': mock_vectorstore,
            'chroma_class': mock_chroma_class
        }


@pytest.fixture
def mock_requests():
    """Mock requests for web scraping."""
    with patch('backend.agents.knowledge_agent.requests') as mock_req:
        mock_response = Mock()
        mock_response.content = b"""
        <html>
            <head><title>InfinitePay Help</title></head>
            <body>
                <article>
                    <h1>Payment Processing</h1>
                    <p>InfinitePay offers comprehensive payment processing solutions including card machines, PIX payments, and transaction management.</p>
                    <p>Our card machine fees are competitive and transparent. Contact support for detailed pricing information.</p>
                </article>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_req.get.return_value = mock_response
        yield mock_req


@pytest.fixture
def conversation_context():
    """Create a test conversation context."""
    return ConversationContext(
        conversation_id="test-conv-123",
        user_id="test-user-456",
        timestamp=datetime.utcnow(),
        message_history=[
            Message(
                content="Hello",
                sender="user",
                timestamp=datetime.utcnow()
            )
        ]
    )


@pytest.fixture
def knowledge_agent(mock_openai_client, mock_embeddings, mock_chroma, mock_requests):
    """Create a KnowledgeAgent instance with mocked dependencies."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
        agent = KnowledgeAgent()
        # Override the async initialization to avoid actual scraping in tests
        agent._initialize_knowledge_base = AsyncMock()
        agent.vectorstore = mock_chroma['vectorstore']
        return agent


class TestKnowledgeAgent:
    """Test cases for KnowledgeAgent."""
    
    def test_initialization(self, mock_openai_client, mock_embeddings, mock_chroma):
        """Test KnowledgeAgent initialization."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = KnowledgeAgent()
            
            assert agent.name == "KnowledgeAgent"
            assert agent.knowledge_base_url == "https://ajuda.infinitepay.io/pt-BR/"
            assert len(agent.keywords) > 0
            assert "infinitepay" in agent.keywords
            assert "payment" in agent.keywords
    
    def test_initialization_without_api_key(self):
        """Test that initialization fails without OpenAI API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is required"):
                KnowledgeAgent()
    
    def test_can_handle_infinitepay_terms(self, knowledge_agent):
        """Test that agent can handle InfinitePay-specific terms with high confidence."""
        test_cases = [
            ("What are InfinitePay card machine fees?", 0.95),
            ("How does the maquininha work?", 0.95),
            ("Tell me about PIX payments", 0.95),
            ("InfinitePay pricing information", 0.95),
        ]
        
        for message, expected_min_confidence in test_cases:
            confidence = knowledge_agent.can_handle(message)
            assert confidence >= expected_min_confidence, f"Failed for message: {message}"
    
    def test_can_handle_general_knowledge_queries(self, knowledge_agent):
        """Test that agent can handle general knowledge queries."""
        test_cases = [
            ("What is payment processing?", 0.6),
            ("How do I set up my account?", 0.6),
            ("Can you help me with integration?", 0.6),
            ("Tell me about your services", 0.6),
        ]
        
        for message, expected_min_confidence in test_cases:
            confidence = knowledge_agent.can_handle(message)
            assert confidence >= expected_min_confidence, f"Failed for message: {message}"
    
    def test_can_handle_non_knowledge_queries(self, knowledge_agent):
        """Test that agent has low confidence for non-knowledge queries."""
        test_cases = [
            "Calculate 5 + 3",
            "What is 10 * 2?",
            "Solve this equation: x + 5 = 10",
            "Random text without context",
        ]
        
        for message in test_cases:
            confidence = knowledge_agent.can_handle(message)
            assert confidence < 0.5, f"Confidence too high for: {message}"
    
    def test_is_valid_help_url(self, knowledge_agent):
        """Test URL validation for help articles."""
        valid_urls = [
            "https://ajuda.infinitepay.io/pt-BR/article/123",
            "https://ajuda.infinitepay.io/pt-BR/guide/setup",
            "https://ajuda.infinitepay.io/pt-BR/faq",
        ]
        
        invalid_urls = [
            "javascript:void(0)",
            "mailto:support@infinitepay.io",
            "https://ajuda.infinitepay.io/pt-BR/download.pdf",
            "https://other-site.com/help",
            "https://ajuda.infinitepay.io/pt-BR/login",
        ]
        
        for url in valid_urls:
            assert knowledge_agent._is_valid_help_url(url), f"Should be valid: {url}"
        
        for url in invalid_urls:
            assert not knowledge_agent._is_valid_help_url(url), f"Should be invalid: {url}"
    
    def test_extract_content_from_page(self, knowledge_agent):
        """Test content extraction from HTML."""
        from bs4 import BeautifulSoup
        
        html_content = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <article>
                    <h1>Payment Processing Guide</h1>
                    <p>This is the main content about payment processing.</p>
                    <p>It includes information about fees and setup.</p>
                </article>
                <script>console.log('should be removed');</script>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        result = knowledge_agent._extract_content_from_page(soup, "https://test.com")
        
        assert result is not None
        assert result['title'] == "Test Article"
        assert "payment processing" in result['content'].lower()
        assert "should be removed" not in result['content']
        assert result['url'] == "https://test.com"
    
    def test_extract_content_from_minimal_page(self, knowledge_agent):
        """Test content extraction from minimal HTML."""
        from bs4 import BeautifulSoup
        
        html_content = "<html><body><p>Too short</p></body></html>"
        soup = BeautifulSoup(html_content, 'html.parser')
        result = knowledge_agent._extract_content_from_page(soup, "https://test.com")
        
        # Should return None for very short content
        assert result is None
    
    def test_create_documents_from_content(self, knowledge_agent):
        """Test document creation from scraped content."""
        knowledge_agent.scraped_content = [
            {
                'title': 'Test Article 1',
                'content': 'This is a test article about payment processing. ' * 50,  # Long enough to split
                'url': 'https://test.com/article1'
            },
            {
                'title': 'Test Article 2',
                'content': 'Short article about fees.',
                'url': 'https://test.com/article2'
            }
        ]
        
        documents = knowledge_agent._create_documents_from_content()
        
        assert len(documents) >= 2  # At least one document per content item
        assert all(doc.metadata['source'] == 'infinitepay_help' for doc in documents)
        assert any('Test Article 1' in doc.metadata['title'] for doc in documents)
        assert any('Test Article 2' in doc.metadata['title'] for doc in documents)
    
    def test_retrieve_relevant_content_no_vectorstore(self, knowledge_agent):
        """Test content retrieval when vectorstore is not initialized."""
        knowledge_agent.vectorstore = None
        
        docs = knowledge_agent._retrieve_relevant_content("test query")
        assert docs == []
    
    def test_retrieve_relevant_content_with_vectorstore(self, knowledge_agent, mock_chroma):
        """Test content retrieval with initialized vectorstore."""
        from langchain.schema import Document
        
        # Mock documents to return
        mock_docs = [
            Document(
                page_content="Information about card machine fees",
                metadata={'title': 'Fees Guide', 'url': 'https://test.com/fees'}
            )
        ]
        
        knowledge_agent.vectorstore.similarity_search.return_value = mock_docs
        
        docs = knowledge_agent._retrieve_relevant_content("card machine fees")
        
        assert len(docs) == 1
        assert docs[0].page_content == "Information about card machine fees"
        knowledge_agent.vectorstore.similarity_search.assert_called_once_with("card machine fees", k=5)
    
    def test_generate_response_with_no_context(self, knowledge_agent):
        """Test response generation when no context documents are available."""
        response = knowledge_agent._generate_response_with_context("test query", [])
        
        assert "don't have specific information" in response
        assert "InfinitePay services" in response
    
    def test_generate_response_with_context(self, knowledge_agent, mock_openai_client):
        """Test response generation with context documents."""
        from langchain.schema import Document
        
        context_docs = [
            Document(
                page_content="Card machine fees are 2.5% per transaction",
                metadata={'title': 'Fees Guide', 'url': 'https://test.com/fees'}
            )
        ]
        
        response = knowledge_agent._generate_response_with_context("What are the fees?", context_docs)
        
        assert response == "This is a test response from the knowledge agent."
        mock_openai_client.chat.completions.create.assert_called_once()
        
        # Check that the prompt includes context
        call_args = mock_openai_client.chat.completions.create.call_args
        prompt = call_args[1]['messages'][1]['content']
        assert "Card machine fees are 2.5% per transaction" in prompt
        assert "What are the fees?" in prompt
    
    @pytest.mark.asyncio
    async def test_process_successful_query(self, knowledge_agent, conversation_context, mock_openai_client):
        """Test successful processing of a knowledge query."""
        from langchain.schema import Document
        
        # Mock the retrieve method to return documents
        mock_docs = [
            Document(
                page_content="InfinitePay card machines have competitive fees",
                metadata={'title': 'Fees Guide', 'url': 'https://test.com/fees'}
            )
        ]
        
        with patch.object(knowledge_agent, '_retrieve_relevant_content', return_value=mock_docs):
            response = await knowledge_agent.process("What are card machine fees?", conversation_context)
        
        assert isinstance(response, AgentResponse)
        assert response.source_agent == "KnowledgeAgent"
        assert response.execution_time > 0
        assert response.content == "This is a test response from the knowledge agent."
        assert response.sources == ['https://test.com/fees']
        assert response.metadata['documents_retrieved'] == 1
        assert response.metadata['processing_method'] == 'rag_retrieval'
    
    @pytest.mark.asyncio
    async def test_process_with_uninitialized_vectorstore(self, knowledge_agent, conversation_context):
        """Test processing when vectorstore is not initialized."""
        knowledge_agent.vectorstore = None
        
        with patch.object(knowledge_agent, '_initialize_knowledge_base', new_callable=AsyncMock) as mock_init:
            with patch.object(knowledge_agent, '_retrieve_relevant_content', return_value=[]):
                response = await knowledge_agent.process("test query", conversation_context)
        
        mock_init.assert_called_once()
        assert isinstance(response, AgentResponse)
    
    @pytest.mark.asyncio
    async def test_process_with_error(self, knowledge_agent, conversation_context):
        """Test processing when an error occurs."""
        # Mock retrieve method to raise an exception
        with patch.object(knowledge_agent, '_retrieve_relevant_content', side_effect=Exception("Test error")):
            response = await knowledge_agent.process("test query", conversation_context)
        
        assert isinstance(response, AgentResponse)
        assert response.source_agent == "KnowledgeAgent"
        assert "encountered an error" in response.content
        assert response.metadata['processing_failed'] is True
        assert "Test error" in response.metadata['error']
    
    @pytest.mark.asyncio
    async def test_scrape_infinitepay_content(self, knowledge_agent, mock_requests):
        """Test scraping of InfinitePay content."""
        # Reset scraped content
        knowledge_agent.scraped_content = []
        
        await knowledge_agent._scrape_infinitepay_content()
        
        assert len(knowledge_agent.scraped_content) > 0
        assert any('InfinitePay' in item['content'] for item in knowledge_agent.scraped_content)
        mock_requests.get.assert_called()
    
    @pytest.mark.asyncio
    async def test_scrape_content_with_request_error(self, knowledge_agent):
        """Test scraping when request fails."""
        with patch('backend.agents.knowledge_agent.requests.get', side_effect=Exception("Network error")):
            await knowledge_agent._scrape_infinitepay_content()
        
        # Should have fallback content
        assert len(knowledge_agent.scraped_content) == 1
        assert 'InfinitePay is a payment processing service' in knowledge_agent.scraped_content[0]['content']
    
    @pytest.mark.asyncio
    async def test_initialize_knowledge_base_with_existing_collection(self, knowledge_agent, mock_chroma):
        """Test initialization when collection already exists."""
        # Mock existing collection with content
        mock_collection = Mock()
        mock_collection.count.return_value = 10
        mock_chroma['client'].get_collection.return_value = mock_collection
        
        await knowledge_agent._initialize_knowledge_base()
        
        # Should not scrape content if collection exists
        assert knowledge_agent.vectorstore is not None
    
    @pytest.mark.asyncio
    async def test_initialize_knowledge_base_error_handling(self, knowledge_agent, mock_chroma):
        """Test initialization error handling."""
        # Mock ChromaDB to raise an error
        mock_chroma['client'].get_collection.side_effect = Exception("ChromaDB error")
        
        with patch.object(knowledge_agent, '_scrape_infinitepay_content', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = Exception("Scraping error")
            
            await knowledge_agent._initialize_knowledge_base()
        
        # Should create empty vectorstore as fallback
        assert knowledge_agent.vectorstore is not None


if __name__ == "__main__":
    pytest.main([__file__])