"""
AegisFlow - RAG Service
Retrieves secure coding guidelines (OWASP) to ground the AI fixes.
"""
import os
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
import google.generativeai as genai

# Custom Embedding Function using Gemini
class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[RAG] No GEMINI_API_KEY found, returning zero vectors (fallback).")
            return [[0.0]*768 for _ in input]
            
        genai.configure(api_key=api_key)
        
        embeddings = []
        for text in input:
            try:
                # Use models/embedding-001 or models/text-embedding-004
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
            except Exception as e:
                print(f"[RAG ERROR] Embedding failed for text chunk: {e}")
                embeddings.append([0.0]*768)
        return embeddings

class RAGService:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.embedding_fn = GeminiEmbeddingFunction()
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="owasp_guidelines",
            embedding_function=self.embedding_fn
        )
        
        # Auto-ingest if empty
        if self.collection.count() == 0:
            self._ingest_data()
            
    def _ingest_data(self):
        """Reads the owasp_guidelines.md and ingests it."""
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "owasp_guidelines.md")
        if not os.path.exists(file_path):
            print(f"[RAG] Guidelines file not found at {file_path}")
            return
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Very simple chunking: split by '## ' (sections)
        chunks = content.split("## ")
        documents = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip(): continue
            documents.append("## " + chunk.strip())
            ids.append(f"owasp_{i}")
            
        if documents:
            self.collection.add(
                documents=documents,
                ids=ids
            )
            print(f"[RAG] Successfully ingested {len(documents)} guidelines into ChromaDB.")
            
    def retrieve_guidelines(self, query: str, n_results: int = 1) -> str:
        """Query the vector database for relevant security guidelines."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if results and results["documents"] and len(results["documents"][0]) > 0:
                # Combine top results into a single string
                context = "\n\n".join(results["documents"][0])
                print(f"[RAG] Retrieved relevant context for query: '{query}'")
                return context
            return ""
        except Exception as e:
            print(f"[RAG ERROR] Retrieval failed: {e}")
            return ""

# Singleton instance
rag_service = RAGService()

def get_rag_context(query: str) -> str:
    return rag_service.retrieve_guidelines(query)
