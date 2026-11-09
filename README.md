# Knowledge Base Agent

A document question-answering assistant built with FastAPI, LangChain, OpenAI, and Pinecone. A static chat interface sends questions to a Python backend, which retrieves relevant document passages and generates an answer grounded in that context.

The intended deployment uses **Vercel** for the backend and **GitHub Pages** for the frontend. Document ingestion runs locally through a separate script.

> This README describes the planned project structure and the supplied backend and frontend examples. Application files and the ingestion script still need to be added.

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

Add the supplied backend dependencies to `api/requirements.txt`:

```text
fastapi
pydantic
uvicorn
langchain
langchain-openai
langchain-pinecone
```

The root `requirements.txt` can include the backend requirements, followed by the loaders and text-splitting dependencies your ingestion script needs:

```text
-r api/requirements.txt
# Add dependencies required by ingestion/ingest.py.
```

Install the local dependencies:

```bash
python -m pip install -r requirements.txt
```

The supplied backend imports retrieval-chain helpers from `langchain.chains`. Confirm that your installed LangChain version supports those imports, or adapt the imports to your chosen version. Pin dependency versions after verifying the application.

### Environment variables

Set these in the terminal where you run the backend and ingestion script:

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

If you prefer a `.env` file, add an environment-loading mechanism to your scripts. The supplied backend reads process environment variables and does not automatically load `.env`.

### Ingest documents

Add your ingestion implementation at `ingestion/ingest.py`, then place documents in `ingestion/data/` and run:

```bash
python ingestion/ingest.py
```

This command assumes the script is designed to run from the repository root. Supported document formats and any command-line options depend on your implementation.

The script should load documents, split them into chunks, generate embeddings with `text-embedding-3-small`, and upload them to the same Pinecone index used by the backend. Keep embedding configuration and any Pinecone namespace consistent between ingestion and retrieval. Use stable vector IDs or another duplicate-handling strategy when re-ingesting documents.

### Run the backend

Save the supplied FastAPI implementation as `api/index.py`, then run from the repository root:

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

Save the supplied interface as `public/index.html`. Set its `BACKEND_URL` to the complete chat endpoint:

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

The supplied endpoint returns HTTP `500` when retrieval or generation fails. FastAPI validates the request body and returns HTTP `422` for invalid input, such as a missing `question` field. The current response contains an answer only; source citations are not included.

## Deployment

### Backend: Vercel

1. Add the backend application and dependency files to the repository.
2. Import the repository into Vercel and configure its Python/FastAPI deployment so requests to `/api/chat` reach `api/index.py`.
3. Add `OPENAI_API_KEY`, `PINECONE_API_KEY`, and `PINECONE_INDEX_NAME` as Vercel environment variables.
4. Deploy and test the public `/api/chat` endpoint.

The directory layout alone does not provide a complete deployment configuration. Verify routing, dependency installation, and serverless execution limits for your Vercel project.

### Frontend: GitHub Pages

1. Set the frontend endpoint to your deployed backend URL:

   ```javascript
   const BACKEND_URL = "https://your-project.vercel.app/api/chat";
   ```

2. Configure GitHub Pages to deploy through GitHub Actions, with a workflow that uploads `public/` as the Pages artifact and deploys it.
3. Open your published Pages URL and test a question.

GitHub Pages branch publishing does not directly select an arbitrary `public/` directory. Use an Actions workflow for this layout, or move the frontend to a supported publishing location.

In the backend CORS configuration, replace the wildcard origin with your frontend origin, for example `https://your-username.github.io`. Origins do not include repository paths.

## Before exposing the application publicly

- Keep API keys on the backend and in your local environment; never put them in frontend JavaScript.
- Add authentication and rate limiting if access should be restricted. CORS alone does not restrict who can call the API.
- Render user and model messages with DOM methods such as `textContent`. The supplied frontend interpolates text into `innerHTML`, which can render untrusted HTML.
- Check `response.ok` in the frontend before treating a response as successful.
- Make backend initialization failures explicit. The supplied initialization handler logs errors but leaves requests unable to use `rag_chain` if setup failed.
- Log detailed errors on the server and return a generic error message to clients.

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
| Ingestion command fails | The script has been added, its dependencies are installed, and document paths match its implementation |
