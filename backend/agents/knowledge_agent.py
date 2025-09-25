import time

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

from agents.base import SpecializedAgent, math_score
from models.core import AgentResponse, ConversationContext


class KnowledgeAgent(SpecializedAgent):
    """Agent that uses Gemini + FAISS retrieval."""

    def __init__(self):
        super().__init__("KnowledgeAgent", keywords=[
            "what", "how", "why", "when", "where", "who", "help", "explain",
            "infinitepay", "payment", "card", "machine", "fees", "support",
            "account", "transaction", "billing", "setup", "configure",
            "problem", "issue", "error", "troubleshoot", "guide", "tutorial"
        ])

        # 1. Load embeddings and FAISS
        embeddings = VertexAIEmbeddings(model_name="text-embedding-004", location="us-central1")
        vectorstore = FAISS.load_local("infinitepay_faiss_index", embeddings, allow_dangerous_deserialization=True)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

        # 2. Build retrieval chain
        llm = ChatVertexAI(model_name="gemini-2.0-flash-001", location="us-central1", temperature=0)
        prompt = ChatPromptTemplate.from_template(
            """You are a helpful assistant with expertise in InfinitePay payment solutions. Use the following context to answer the user's question:
CONTEXT:
{context}
USER QUESTION: {input}
Please provide a helpful, accurate response based on the context provided. If the question is about InfinitePay, use the context information. If using the context information, say the information comes from https://ajuda.infinitepay.io/pt-BR/. For general questions, provide helpful information while being concise and clear."""
        )
        document_chain = create_stuff_documents_chain(llm, prompt)
        self.retrieval_chain = create_retrieval_chain(retriever, document_chain)

    def can_handle(self, message: str) -> float:
        """Return a score indicating how likely this is a knowledge question."""
        # Inverse: high when math score is low
        return 1.0 - math_score(message)

    async def process(self, message: str, context: ConversationContext) -> AgentResponse:
        start_time = time.perf_counter()

        # run RAG pipeline asynchronously
        result = await self.retrieval_chain.ainvoke({"input": message})

        execution_time = time.perf_counter() - start_time
        answer = result["answer"]
        docs = result["context"]

        sources = [d.metadata.get("source") for d in docs if d.metadata.get("source")]
        metadata = {
            "titles": [d.metadata.get("title") for d in docs],
            "conversation_id": context.conversation_id,
            "user_id": context.user_id,
        }

        return AgentResponse(
            content=answer,
            source_agent=self.name,
            execution_time=execution_time,
            metadata=metadata,
            sources=sources
        )
