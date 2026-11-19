# Enterprise Knowledge Intelligence Platform

A local-first Retrieval-Augmented Generation (RAG) application built with React, FastAPI, Sentence Transformers, FAISS, and Ollama. The project includes automated backend tests, Docker Compose support, and a GitHub Actions CI workflow.

## Prerequisites

- Python 3.11–3.13 for local development (the Docker image uses Python 3.12)
- Node.js 22+
- Ollama installed and running on your Mac
- Docker Desktop for the containerized setup

## Option A — Run locally

### 1. Start Ollama

In one terminal, run:

```bash
ollama serve
```

In a second terminal, make sure the model is available:

```bash
ollama pull llama3.2:3b
ollama list
```

### 2. Start the backend

From the project root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

The first startup downloads the embedding model `sentence-transformers/all-MiniLM-L6-v2`. API docs: <http://127.0.0.1:8000/docs>.

### 3. Start the frontend

Open a new terminal from the project root:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open <http://localhost:5173>.

## Option B — Run with Docker Compose

Docker Compose runs the API and production-built React frontend in containers. Ollama remains on your Mac host, so start it first and ensure `llama3.2:3b` is downloaded.

From the project root:

```bash
docker compose up --build
```

Open:

- Frontend: <http://localhost:5173>
- API docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

The first backend startup inside Docker downloads the embedding model and may take several minutes. Named Docker volumes preserve uploaded/indexed data and the Hugging Face model cache across container restarts. Stop the containers with `Ctrl+C`; to stop and remove containers, run `docker compose down`. To also delete stored project data, run `docker compose down -v` (this permanently deletes the named volumes).

If the container cannot reach Ollama, confirm Ollama is listening on port 11434 on the host and run `ollama list`. The Compose configuration connects to `host.docker.internal:11434`.

## Automated tests

Run from the project root:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
```

The API tests use a fake vector store and a stubbed answer generator, so they don't need a live Ollama model or a model download. They test the health endpoint, empty document list, file validation, upload/list/chat/delete flow, and missing-document behavior.

The GitHub Actions workflow in `.github/workflows/ci.yaml` runs backend tests and builds the frontend on pushes and pull requests.

## Try it

Upload `sample_data/employee_handbook.txt`, then ask:

- How many days of annual leave are provided?
- What are the remote work rules?
- What is the process for reporting a security incident?
- What is the company's parental leave policy? (It should say there is insufficient evidence.)

## API endpoints

- `GET /health`
- `GET /documents`
- `POST /documents/upload`
- `POST /chat`
- `DELETE /documents/{document_id}`

## Current limitations

- Single-user prototype; authentication and authorization are not implemented.
- Scanned PDFs require OCR, which is not included.
- Similarity scores are ranking signals, not confidence probabilities.
- Ollama must run separately on the host for the Docker setup.
- Not yet deployed to Azure; do not upload confidential company documents.

## Roadmap

1. Local RAG baseline — complete
2. Dockerized app, automated tests, and CI — in progress
3. Retrieval evaluation, reranking, and persistence hardening
4. Azure deployment with secure configuration and cost controls
