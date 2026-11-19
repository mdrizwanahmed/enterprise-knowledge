"""API tests use a fake vector store so they don't download ML models or call Ollama."""
import pytest
from fastapi.testclient import TestClient

from app import main


class FakeVectorStore:
    def __init__(self):
        self.chunks = []

    def add_chunks(self, chunks):
        self.chunks.extend(chunks)

    def search(self, query, top_k=4):
        return [(chunk, 0.91) for chunk in self.chunks[:top_k]]

    def remove_document(self, document_id):
        self.chunks = [c for c in self.chunks if c.document_id != document_id]


@pytest.fixture
def client(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setattr(main, "UPLOAD_DIR", uploads)
    monkeypatch.setattr(main, "DOCS_FILE", tmp_path / "documents.json")
    monkeypatch.setattr(main, "LocalVectorStore", FakeVectorStore)
    monkeypatch.setattr(main, "generate_answer", lambda question, contexts: "Annual leave is 20 days. [Source 1]")
    with TestClient(main.app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_documents_initially_empty(client):
    response = client.get("/documents")
    assert response.status_code == 200
    assert response.json() == {"documents": []}


def test_rejects_unsupported_file_type(client):
    response = client.post(
        "/documents/upload",
        files={"file": ("payload.exe", b"not allowed", "application/octet-stream")},
    )
    assert response.status_code == 415


def test_rejects_empty_upload(client):
    response = client.post(
        "/documents/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_chat_and_delete_document(client):
    content = b"Annual leave policy: full-time employees receive 20 days of annual leave."
    upload = client.post(
        "/documents/upload",
        files={"file": ("handbook.txt", content, "text/plain")},
    )
    assert upload.status_code == 200, upload.text
    document = upload.json()
    assert document["filename"] == "handbook.txt"
    assert document["chunks"] >= 1

    listed = client.get("/documents").json()["documents"]
    assert len(listed) == 1
    assert listed[0]["document_id"] == document["document_id"]

    chat = client.post("/chat", json={"question": "How many annual leave days?", "top_k": 4})
    assert chat.status_code == 200, chat.text
    assert "20 days" in chat.json()["answer"]
    assert chat.json()["citations"][0]["filename"] == "handbook.txt"

    deleted = client.delete(f"/documents/{document['document_id']}")
    assert deleted.status_code == 200
    assert client.get("/documents").json()["documents"] == []


def test_delete_unknown_document_returns_404(client):
    response = client.delete("/documents/not-a-real-id")
    assert response.status_code == 404
