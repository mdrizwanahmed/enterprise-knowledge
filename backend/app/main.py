from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4
import json
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from app.chunking import split_text
from app.config import ALLOWED_EXTENSIONS, CHUNK_OVERLAP, CHUNK_SIZE, MAX_UPLOAD_MB, UPLOAD_DIR
from app.document_parser import extract_pages
from app.rag import generate_answer
from app.schemas import ChatRequest, ChatResponse
from app.vector_store import Chunk, LocalVectorStore

store = None
DOCS_FILE = UPLOAD_DIR.parent / "documents.json"

def read_documents():
    return json.loads(DOCS_FILE.read_text(encoding="utf-8")) if DOCS_FILE.exists() else []

def write_documents(items):
    DOCS_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global store
    store = LocalVectorStore()
    yield

app = FastAPI(title="Enterprise Knowledge Intelligence API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=False, allow_methods=["GET", "POST", "DELETE"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "enterprise-knowledge-intelligence"}

@app.get("/documents")
def list_documents():
    return {"documents": read_documents()}

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    if store is None:
        raise HTTPException(status_code=503, detail="Vector store is still starting.")
    filename = Path(file.filename or "upload").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds the {MAX_UPLOAD_MB} MB upload limit.")
    document_id = str(uuid4())
    path = UPLOAD_DIR / f"{document_id}{suffix}"
    path.write_bytes(contents)
    try:
        pages = extract_pages(path)
        chunks = []
        chunk_id = 0
        for page in pages:
            for text in split_text(page["text"], CHUNK_SIZE, CHUNK_OVERLAP):
                chunks.append(Chunk(document_id, filename, chunk_id, page["page"], text))
                chunk_id += 1
        if not chunks:
            raise ValueError("No readable text found. Scanned PDFs may require OCR.")
        store.add_chunks(chunks)
    except ValueError as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        path.unlink(missing_ok=True)
        raise
    items = read_documents()
    record = {"document_id": document_id, "filename": filename, "chunks": len(chunks), "bytes": len(contents)}
    items.append(record)
    write_documents(items)
    return {"message": "Document indexed successfully.", **record}

@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    if store is None:
        raise HTTPException(status_code=503, detail="Vector store is still starting.")
    results = [(c, s) for c, s in store.search(payload.question, payload.top_k) if s >= 0.25]
    contexts = [{"filename": c.filename, "page": c.page, "text": c.text} for c, _ in results]
    try:
        answer = generate_answer(payload.question, contexts)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    citations = [{"document_id": c.document_id, "filename": c.filename, "chunk_id": c.chunk_id, "page": c.page, "excerpt": c.text[:360] + ("…" if len(c.text) > 360 else ""), "score": round(s, 4)} for c, s in results]
    return ChatResponse(answer=answer, citations=citations)

@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    if store is None:
        raise HTTPException(status_code=503, detail="Vector store is still starting.")
    items = read_documents()
    target = next((item for item in items if item["document_id"] == document_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    store.remove_document(document_id)
    for path in UPLOAD_DIR.glob(f"{document_id}.*"):
        path.unlink(missing_ok=True)
    write_documents([item for item in items if item["document_id"] != document_id])
    return {"message": "Document deleted.", "document_id": document_id}
