from dataclasses import dataclass
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL, INDEX_DIR

@dataclass
class Chunk:
    document_id: str
    filename: str
    chunk_id: int
    page: int | None
    text: str

class LocalVectorStore:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.chunks = []
        self.index = None
        self.metadata_path = INDEX_DIR / "chunks.json"
        self.index_path = INDEX_DIR / "vectors.faiss"
        if self.metadata_path.exists() and self.index_path.exists():
            self.chunks = [Chunk(**x) for x in json.loads(self.metadata_path.read_text(encoding="utf-8"))]
            self.index = faiss.read_index(str(self.index_path))

    def _persist(self):
        self.metadata_path.write_text(json.dumps([c.__dict__ for c in self.chunks], ensure_ascii=False, indent=2), encoding="utf-8")
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_path))
        elif self.index_path.exists():
            self.index_path.unlink()

    def _rebuild(self):
        self.index = None
        if self.chunks:
            vectors = self.model.encode([c.text for c in self.chunks], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).astype("float32")
            self.index = faiss.IndexFlatIP(vectors.shape[1])
            self.index.add(vectors)
        self._persist()

    def add_chunks(self, chunks):
        if chunks:
            self.chunks.extend(chunks)
            self._rebuild()

    def remove_document(self, document_id):
        self.chunks = [c for c in self.chunks if c.document_id != document_id]
        self._rebuild()

    def search(self, query, top_k=4):
        if self.index is None or not self.chunks:
            return []
        vector = self.model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype("float32")
        scores, indices = self.index.search(vector, min(top_k, len(self.chunks)))
        return [(self.chunks[int(i)], float(s)) for s, i in zip(scores[0], indices[0]) if i >= 0]
