"""Obsidian RAG용 ChromaDB 관리 모듈."""

import json
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

from .chunker import Chunk
from .config import get_chroma_db_path

COLLECTION_NAME = "obsidian_vault"


class ChromaManager:
    """Obsidian RAG를 위한 ChromaDB 작업 관리 클래스."""

    def __init__(self, db_path: Optional[Path] = None):
        """ChromaDB 클라이언트를 초기화한다."""
        self.db_path = db_path or get_chroma_db_path()
        self.db_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[Chunk]) -> int:
        """청크들을 컬렉션에 추가한다.

        Returns:
            추가된 청크 수
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
        """파일의 모든 청크를 업데이트한다.

        기존 청크를 삭제하고 새 청크를 추가한다.

        Returns:
            (삭제된 청크 수, 추가된 청크 수) 튜플
        """
        deleted = self.delete_file(file_path)
        added = self.add_chunks(chunks)
        return deleted, added

    def delete_file(self, file_path: str) -> int:
        """파일의 모든 청크를 삭제한다.

        Returns:
            삭제된 청크 수
        """
        # 해당 파일의 모든 청크 조회
        results = self.collection.get(where={"file_path": file_path})

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            return len(results["ids"])
        return 0

    def search(
        self, query: str, top_k: int = 5, file_filter: Optional[str] = None
    ) -> list[dict]:
        """유사한 청크를 검색한다.

        Args:
            query: 검색 쿼리 텍스트
            top_k: 반환할 결과 수
            file_filter: 결과를 필터링할 파일 경로 접두사 (선택)

        Returns:
            검색 결과 딕셔너리 리스트
        """
        # 필터가 있으면 더 많이 검색 후 필터링
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

                # 파일 필터 적용
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

                # top_k 개수 제한
                if len(output) >= top_k:
                    break

        return output

    def get_stats(self) -> dict:
        """컬렉션 통계를 반환한다."""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": COLLECTION_NAME,
            "db_path": str(self.db_path),
        }

    def clear(self) -> int:
        """컬렉션의 모든 데이터를 삭제한다.

        Returns:
            삭제된 청크 수
        """
        count = self.collection.count()
        if count > 0:
            # 모든 ID를 가져와서 삭제
            all_ids = self.collection.get()["ids"]
            if all_ids:
                self.collection.delete(ids=all_ids)
        return count
