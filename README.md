# Knowledge Base Agent

A public customer FAQ assistant for Ink & Anchor Tattoo Studio, built with FastAPI, LangChain, OpenAI, and Pinecone. A static chat interface sends questions to a Python backend, which retrieves relevant document passages and generates an answer grounded in that context.

## Try the app

Use either frontend—no customer login is required:

- [GitHub Pages](https://bryantserrano.github.io/knowledge-base-agent/)
- [Vercel](https://knowledge-base-agent-ashy.vercel.app/)

Ask about studio hours, deposits, rescheduling, cancellations, or touch-ups. Both interfaces use the same Vercel backend and customer FAQ namespace. Chat may be temporarily unavailable when disabled by the administrator.

Vercel hosts the backend and a copy of the frontend; GitHub Pages hosts the static frontend. Document ingestion runs locally through a separate script.

> The backend, frontend, ingestion script, and GitHub Pages workflow are included. Configure credentials and ingest documents before asking questions. Use Python 3.12; the Pinecone integration does not support Python 3.14 or 3.15.

## How it works

1. Place approved customer FAQ documents in `ingestion/faqs/`.
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
│   ├── data/                # Original private documents; excluded from FAQ ingestion
│   ├── faqs/                # Approved customer FAQs; tracked in Git
│   └── ingest.py            # Customer FAQ ingestion script
├── public/
│   └── index.html           # Static chat interface
├── .gitignore
├── README.md
└── requirements.txt         # Local development and ingestion dependencies
```

## Prerequisites

- Python 3.12 and a virtual environment (the version is recorded in `.python-version`).
- An OpenAI API key.
- A Pinecone API key and an existing index configured for your embedding output dimensions.
- Vercel and GitHub accounts for deployment.

OpenAI and Pinecone usage may incur charges.

## Local setup

From the repository root, create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with `.venv\Scripts\Activate.ps1`.

Alternatively, if you use `uv`:

```bash
uv python install 3.12
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install --python .venv/bin/python -r requirements.txt
```

`uv venv` does not install `pip` by default; use `uv pip` to install dependencies in that environment.

Backend dependencies are defined in `api/requirements.txt`:

```text
fastapi>=0.115,<1
pydantic>=2,<3
uvicorn>=0.30,<1
langchain-core>=1,<2
langchain-openai>=1,<2
langchain-pinecone>=0.2,<1
pinecone>=6,<8
python-dotenv>=1,<2
```

The root `requirements.txt` explicitly lists backend dependencies plus PDF/DOCX readers and text splitters for local ingestion. Keep its backend entries synchronized with `api/requirements.txt`. Avoid nested `-r` includes here because Vercel's requirements parsing failed on that layout during deployment.

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
export PINECONE_INDEX_NAME="knowledge-base"
export PINECONE_NAMESPACE="customer-faqs"
export CHAT_ENABLED="true"
```

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI embeddings and chat generation |
| `PINECONE_API_KEY` | Access to the Pinecone index |
| `PINECONE_INDEX_NAME` | Pinecone index name: `knowledge-base` |
| `PINECONE_NAMESPACE` | Collection inside the index: `customer-faqs` |
| `CHAT_ENABLED` | Set `false` to disable chat; defaults to `true` |
| `ALLOWED_ORIGINS` | Comma-separated frontend origins permitted by browser CORS |

Both scripts load `.env`. `PINECONE_NAMESPACE` defaults to `customer-faqs`. Set `ALLOWED_ORIGINS` to a comma-separated list of frontend origins. Create the Pinecone index with 1536 dimensions and cosine similarity for the default embedding configuration.

### Enable or disable chat

Set `CHAT_ENABLED=false` to disable `/api/chat`. It returns HTTP `503` with
`{"detail":"Chat is temporarily unavailable."}` before retrieval or generation.
Disabled startup skips OpenAI/Pinecone initialization, so it works without provider
credentials or connectivity. `/api/health` remains available and includes
`chat_enabled`.

Set `CHAT_ENABLED=true` to enable chat. If omitted, it defaults to enabled;
values other than `true` (ignoring case and whitespace) disable it. The setting
is read at startup. Restart the backend after changing local `.env` values.
In Vercel, change **Settings → Environment Variables → CHAT_ENABLED** for the
appropriate environment, then redeploy. Existing deployments keep their previous
setting; the flag does not cancel requests already in progress.

### Ingest customer FAQs

The public assistant reads only the configured FAQ namespace. Original records in the `documents` namespace are preserved and excluded when using `customer-faqs`. The script ingests only `ingestion/faqs/`; review every file in that directory before uploading. Its contents are tracked in Git. Set `PINECONE_NAMESPACE=customer-faqs` in your deployed backend environment too, then redeploy. Local `.env` changes do not update Vercel.


Place approved customer-facing PDF, DOCX, or UTF-8 TXT documents in `ingestion/faqs/` and run:

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

The committed frontend points to the production backend. To test against your local backend, temporarily change `BACKEND_URL` in `public/index.html` to:

```javascript
const BACKEND_URL = "http://localhost:8000/api/chat";
```

Serve the frontend in another terminal:

```bash
python -m http.server 8080 --directory public
```

Open <http://localhost:8080> and send a question. Restore the production backend URL before publishing.

## API

### `POST /api/chat`

Request body:

```json
{
  "question": "What are the studio working hours?"
}
```

Successful response:

```json
{
  "answer": "An answer generated from the retrieved document context."
}
```

The endpoint returns HTTP `503` when chat is disabled and HTTP `502` when retrieval or generation fails. `GET /api/health` reports application readiness after startup; it does not check provider availability on each call. FastAPI validates the request body and returns HTTP `422` for invalid input, such as a missing `question` field. The current response contains an answer only; source citations are not included.

## Deployment

### Backend: Vercel

1. Push the application files to your repository.
2. Import the repository into Vercel and configure its Python/FastAPI deployment so requests to `/api/chat` reach `api/index.py`.
3. Add `OPENAI_API_KEY`, `PINECONE_API_KEY`, and `PINECONE_INDEX_NAME` as Vercel environment variables. Set `PINECONE_NAMESPACE` consistently and `ALLOWED_ORIGINS` to your GitHub Pages origin.
4. Deploy, check `/api/health`, and test the public `/api/chat` endpoint.

Production configuration (add real keys in Vercel, never in this file):

```dotenv
OPENAI_API_KEY=your-openai-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=knowledge-base
PINECONE_NAMESPACE=customer-faqs
CHAT_ENABLED=true
ALLOWED_ORIGINS=https://bryantserrano.github.io,https://knowledge-base-agent-ashy.vercel.app
```

`knowledge-base` is the **index**, while `customer-faqs` is the **namespace inside it**. Using the namespace as `PINECONE_INDEX_NAME` causes a Pinecone `404 Resource customer-faqs not found` during startup. The API key must belong to the project containing the index.

Environment variables in local `.env` are not uploaded automatically. Set the Production environment variables in Vercel and redeploy after changes.

Use the stable production domain, `https://knowledge-base-agent-ashy.vercel.app`, rather than a generated per-deployment URL. Under Standard Protection, generated URLs may require Vercel sign-in. The customer-facing production API must be publicly accessible; check its health endpoint in a private browser window:

[Production API health](https://knowledge-base-agent-ashy.vercel.app/api/health)

Expected when enabled:

```json
{"status":"ok","chat_enabled":true}
```

A healthy startup does not verify answer generation. Ask a known FAQ from each frontend to test the full flow. The Vercel deployment can also serve the static interface from `public/`.


The `api/index.py` entrypoint uses Vercel’s FastAPI support. See the [Vercel FastAPI deployment guide](https://vercel.com/docs/frameworks/backend/fastapi). Verify the deployment logs and execution limits for your project.

### Frontend: GitHub Pages

1. Set the frontend endpoint to your deployed backend URL:

   ```javascript
   const BACKEND_URL = "https://knowledge-base-agent-ashy.vercel.app/api/chat";
   ```

2. Select **GitHub Actions** as the Pages publishing source in repository settings. The included `.github/workflows/pages.yml` deploys `public/` on pushes to `main` or manual runs.
3. Open your published Pages URL and test a question.

GitHub Pages branch publishing does not directly select an arbitrary `public/` directory. Use an Actions workflow for this layout, or move the frontend to a supported publishing location.

Configure `ALLOWED_ORIGINS` with both frontend origins shown above. Origins do not include repository paths, so use `https://bryantserrano.github.io`, without `/knowledge-base-agent/`.

## Before exposing the application publicly

- Keep API keys on the backend and in your local environment; never put them in frontend JavaScript.
- The customer FAQ chat is public and does not require login. Ingest only approved public content. Rate limiting is not implemented in the app; configure abuse controls before broader promotion. CORS and prompt instructions do not authenticate callers.
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
| Pinecone reports `Resource customer-faqs not found` | Set index to `knowledge-base`, namespace to `customer-faqs`, then redeploy |
| API redirects to Vercel login | Use the production domain and check Deployment Protection settings |
| GitHub Actions reports Pages site not found | Select GitHub Actions under repository Settings → Pages → Source, then rerun the workflow |
| Health returns `FUNCTION_INVOCATION_FAILED` | Inspect Vercel runtime logs for the startup traceback and verify Production environment variables |
| Chat returns HTTP `503` | Check `CHAT_ENABLED`; set `true` and restart or redeploy to enable |
| Browser cannot connect | Full backend URL including `/api/chat`, deployment routing, and CORS origin |
| Answers lack useful context | Successful ingestion, matching embedding configuration, index, and namespace |
| Requests return server errors | Backend logs, provider credentials, quotas, and serverless time limits |
| Ingestion command fails | Dependencies are installed and PDF/DOCX/TXT files exist in ingestion/faqs/ |
