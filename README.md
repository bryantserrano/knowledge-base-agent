# Knowledge Base Agent

A document question-answering assistant built with FastAPI, LangChain, OpenAI, and Pinecone. A static chat interface sends questions to a Python backend, which retrieves relevant document passages and generates an answer grounded in that context.

The intended deployment uses **Vercel** for the backend and **GitHub Pages** for the frontend. Document ingestion runs locally through a separate script.

> The backend, frontend, ingestion script, and GitHub Pages workflow are included. Configure credentials and ingest documents before asking questions. Use Python 3.10 or newer.

## How it works

1. Place source documents in `ingestion/data/`.
2. Run your ingestion script to load, chunk, embed, and upload documents to Pinecone.
3. Ask a question through the browser interface.
4. The backend embeds the question and retrieves the three most relevant chunks.
5. OpenAI generates an answer using the retrieved context. The prompt instructs it to say it does not know when the context is insufficient.

The supplied backend uses `text-embedding-3-small` for embeddings and `gpt-4o-mini` for answers, with a temperature of `0.3`. Each request is independent; the displayed chat history is not sent to the backend.

## Project structure

```text
knowledge-base-agent/
├── .github/workflows/       # Optional CI/CD automation
├── api/
│   ├── index.py             # FastAPI app with LangChain and Pinecone
│   └── requirements.txt     # Backend dependencies
├── ingestion/
│   ├── data/                # Local Word/PDF documents; git-ignored
│   └── ingest.py            # Your document ingestion script
├── public/
│   └── index.html           # Static chat interface
├── .gitignore
├── README.md
└── requirements.txt         # Local development and ingestion dependencies
```

## Prerequisites

- Python and a virtual environment.
- An OpenAI API key.
- A Pinecone API key and an existing index configured for your embedding output dimensions.
- Vercel and GitHub accounts for deployment.

OpenAI and Pinecone usage may incur charges.

## Local setup

From the repository root, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with `.venv\Scripts\Activate.ps1`.

Backend dependencies are defined in `api/requirements.txt`:

```text
fastapi>=0.115,<1
pydantic>=2,<3
uvicorn>=0.30,<1
langchain-openai>=1,<2
langchain-pinecone>=0.2,<1
python-dotenv>=1,<2
```

The root `requirements.txt` includes backend dependencies plus PDF/DOCX loaders and text splitters for local ingestion.

Install the local dependencies:

```bash
python -m pip install -r requirements.txt
```

Retrieval and generation use the LangChain integration packages directly, without the legacy `langchain.chains` helpers.

### Environment variables

Copy `.env.example` to `.env` and fill in your credentials, or export these variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export PINECONE_API_KEY="your-pinecone-api-key"
export PINECONE_INDEX_NAME="your-index-name"
```

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI embeddings and chat generation |
| `PINECONE_API_KEY` | Access to the Pinecone index |
| `PINECONE_INDEX_NAME` | Name of the index containing document vectors |

Both scripts load `.env`. `PINECONE_NAMESPACE` defaults to `documents`. Set `ALLOWED_ORIGINS` to a comma-separated list of frontend origins. Create the Pinecone index with 1536 dimensions and cosine similarity for the default embedding configuration.

### Ingest documents

Place PDF or DOCX documents in `ingestion/data/` and run:

```bash
python ingestion/ingest.py
```

The script resolves document paths relative to the repository, including nested directories. Legacy `.doc` files are not supported.

The script splits documents into 1000-character chunks with 200 characters of overlap and uploads embeddings to the configured index and namespace. Stable IDs prevent duplicate vectors for unchanged chunks. Modified or removed documents can leave old vectors behind; clean up those vectors before replacing a document collection.

### Run the backend

Run from the repository root:

```bash
python -m uvicorn api.index:app --reload --port 8000
```

Interactive API documentation is available at <http://localhost:8000/docs>.

Test the chat endpoint after ingesting documents:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What do the documents cover?"}'
```

### Run the frontend

The interface in `public/index.html` defaults to the local chat endpoint:

```javascript
const BACKEND_URL = "http://localhost:8000/api/chat";
```

Serve the frontend in another terminal:

```bash
python -m http.server 8080 --directory public
```

Open <http://localhost:8080> and send a question.

## API

### `POST /api/chat`

Request body:

```json
{
  "question": "What is the document retention policy?"
}
```

Successful response:

```json
{
  "answer": "An answer generated from the retrieved document context."
}
```

The endpoint returns HTTP `502` when retrieval or generation fails. `GET /api/health` reports application readiness after startup; it does not check provider availability on each call. FastAPI validates the request body and returns HTTP `422` for invalid input, such as a missing `question` field. The current response contains an answer only; source citations are not included.

## Deployment

### Backend: Vercel

1. Push the application files to your repository.
2. Import the repository into Vercel and configure its Python/FastAPI deployment so requests to `/api/chat` reach `api/index.py`.
3. Add `OPENAI_API_KEY`, `PINECONE_API_KEY`, and `PINECONE_INDEX_NAME` as Vercel environment variables. Set `PINECONE_NAMESPACE` consistently and `ALLOWED_ORIGINS` to your GitHub Pages origin.
4. Deploy and test the public `/api/chat` endpoint.

The `api/index.py` entrypoint uses Vercel’s FastAPI support. See the [Vercel FastAPI deployment guide](https://vercel.com/docs/frameworks/backend/fastapi). Verify the deployment logs and execution limits for your project.

### Frontend: GitHub Pages

1. Set the frontend endpoint to your deployed backend URL:

   ```javascript
   const BACKEND_URL = "https://your-project.vercel.app/api/chat";
   ```

2. Select **GitHub Actions** as the Pages publishing source in repository settings. The included `.github/workflows/pages.yml` deploys `public/` on pushes to `main` or manual runs.
3. Open your published Pages URL and test a question.

GitHub Pages branch publishing does not directly select an arbitrary `public/` directory. Use an Actions workflow for this layout, or move the frontend to a supported publishing location.

In the backend CORS configuration, replace the wildcard origin with your frontend origin, for example `https://your-username.github.io`. Origins do not include repository paths.

## Before exposing the application publicly

- Keep API keys on the backend and in your local environment; never put them in frontend JavaScript.
- Add authentication and rate limiting if access should be restricted. CORS alone does not restrict who can call the API.
- The frontend renders messages with `textContent` and checks HTTP errors. The backend validates questions, fails startup on missing configuration, logs provider errors, and returns generic error messages.

## Git ignore rules

Add these entries to `.gitignore` before committing credentials or source documents:

```gitignore
.env
.env.*
!.env.example
.venv/
__pycache__/
*.py[cod]
ingestion/data/
.vercel/
```

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Backend fails during initialization | Environment variables, Pinecone index access, and LangChain import compatibility |
| Browser cannot connect | Full backend URL including `/api/chat`, deployment routing, and CORS origin |
| Answers lack useful context | Successful ingestion, matching embedding configuration, index, and namespace |
| Requests return server errors | Backend logs, provider credentials, quotas, and serverless time limits |
| Ingestion command fails | Dependencies are installed and PDF/DOCX files exist in ingestion/data/ |
