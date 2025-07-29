from typing import List, Optional
import chromadb
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.models import Chapter
from app.config import settings

class VectorStore:
    """Manages vector database operations"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self.chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    
    def get_or_create_collection(self, book_id: str):
        """Get or create a collection for a book"""
        collection_name = f"book_{book_id}"
        try:
            return self.chroma_client.get_collection(collection_name)
        except:
            return self.chroma_client.create_collection(
                name=collection_name,
                embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=settings.embedding_model
                )
            )
    
    def index_chapters(self, book_id: str, chapters: List[Chapter]):
        """Index chapters in vector database"""
        collection = self.get_or_create_collection(book_id)
        
        for chapter in chapters:
            # Split chapter into chunks
            chunks = self.text_splitter.split_text(chapter.content)
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "chapter_number": chapter.chapter_number,
                    "chapter_title": chapter.title,
                    "page_start": chapter.page_start,
                    "page_end": chapter.page_end,
                    "chunk_index": i
                })
                ids.append(f"ch{chapter.chapter_number}_chunk{i}")
            
            # Add to collection
            if documents:  # Only add if there are documents
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
    
    def search(self, book_id: str, query: str, n_results: int = 5, chapter_filter: Optional[int] = None):
        """Search for relevant content"""
        collection = self.get_or_create_collection(book_id)
        
        where_clause = {"chapter_number": chapter_filter} if chapter_filter else None
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_clause
        )
        
        return results
