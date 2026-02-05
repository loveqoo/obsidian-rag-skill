"""ChromaDB management module for Obsidian RAG."""

import json
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from .chunker import Chunk
from .config import get_chroma_db_path

# Multilingual embedding model for better Korean support
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
# Collection name includes model info to avoid conflicts when model changes
COLLECTION_NAME = "obsidian_vault_multilingual"


class ChromaManager:
    """Manages ChromaDB operations for Obsidian RAG."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the ChromaDB client."""
        self.db_path = db_path or get_chroma_db_path()
        self.db_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False),
        )

        # Use multilingual embedding function for better Korean support
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[Chunk]) -> int:
        """Add chunks to the collection.

        Returns:
            Number of chunks added.
        """
        if not chunks:
            return 0

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = f"{chunk.file_path}::{chunk.chunk_index}"
            ids.append(chunk_id)
            documents.append(chunk.content)
            metadatas.append(
                {
                    "file_path": chunk.file_path,
                    "chunk_index": chunk.chunk_index,
                    "heading": chunk.heading,
                    "heading_level": chunk.heading_level,
                    "title": chunk.metadata.get("title", ""),
                    "tags": json.dumps(chunk.metadata.get("tags", [])),
                }
            )

        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
        return len(chunks)

    def update_file(self, file_path: str, chunks: list[Chunk]) -> tuple[int, int]:
        """Update all chunks for a file.

        Deletes existing chunks and adds new ones.

        Returns:
            Tuple of (deleted chunk count, added chunk count).
        """
        deleted = self.delete_file(file_path)
        added = self.add_chunks(chunks)
        return deleted, added

    def delete_file(self, file_path: str) -> int:
        """Delete all chunks for a file.

        Returns:
            Number of chunks deleted.
        """
        # Query all chunks for this file
        results = self.collection.get(where={"file_path": file_path})

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            return len(results["ids"])
        return 0

    def search(
        self, query: str, top_k: int = 5, file_filter: Optional[str] = None
    ) -> list[dict]:
        """Search for similar chunks.

        Args:
            query: Search query text.
            top_k: Number of results to return.
            file_filter: Optional file path prefix to filter results.

        Returns:
            List of search result dictionaries.
        """
        # Search more if filter is applied, then filter
        search_k = top_k * 3 if file_filter else top_k

        results = self.collection.query(
            query_texts=[query],
            n_results=search_k,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                # Apply file filter
                file_path = metadata.get("file_path", "")
                if file_filter and file_filter not in file_path:
                    continue

                tags = metadata.get("tags", "[]")
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except json.JSONDecodeError:
                        tags = []

                output.append(
                    {
                        "file_path": file_path,
                        "chunk_index": metadata.get("chunk_index", 0),
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                        "metadata": {
                            "title": metadata.get("title", ""),
                            "tags": tags,
                            "heading": metadata.get("heading", ""),
                        },
                    }
                )

                # Limit to top_k
                if len(output) >= top_k:
                    break

        return output

    def get_stats(self) -> dict:
        """Return collection statistics."""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": COLLECTION_NAME,
            "db_path": str(self.db_path),
        }

    def clear(self) -> int:
        """Delete all data from the collection.

        Returns:
            Number of chunks deleted.
        """
        count = self.collection.count()
        if count > 0:
            # Get all IDs and delete
            all_ids = self.collection.get()["ids"]
            if all_ids:
                self.collection.delete(ids=all_ids)
        return count
