from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import chromadb
from chromadb.config import Settings
from google import genai
from google.genai import types

COLLECTION_NAME = "jaipur_places"


class RAGSearchTool:
    def __init__(self, data_path: str, persist_dir: str) -> None:
        self._genai = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self._embed_model = os.environ["GEMINI_EMBED_MODEL"]
        self._chroma = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._chroma.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        if self._collection.count() == 0:
            self._ingest(data_path)

    def _embed(self, texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        result = self._genai.models.embed_content(
            model=self._embed_model,
            contents=texts,
            config=types.EmbedContentConfig(task_type=task),
        )
        return [e.values for e in result.embeddings]

    def _ingest(self, path: str) -> None:
        text = Path(path).read_text(encoding="utf-8")
        chunks = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 50]
        embeddings = self._embed(chunks)
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        self._collection.add(documents=chunks, embeddings=embeddings, ids=ids)
        print(f"[RAG] Ingested {len(chunks)} chunks from {path}", file=sys.stderr, flush=True)

    def search(self, query: str, top_k: int = 3) -> str:
        q_embed = self._embed([query], task="RETRIEVAL_QUERY")
        results = self._collection.query(query_embeddings=q_embed, n_results=top_k)
        docs = results["documents"][0]
        distances = results["distances"][0]
        output = [
            {"rank": i + 1, "score": round(1 - d, 4), "text": doc}
            for i, (doc, d) in enumerate(zip(docs, distances))
        ]
        return json.dumps(output, ensure_ascii=False, indent=2)
