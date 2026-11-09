"""Upload local PDF and DOCX documents to Pinecone."""

import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

ROOT = Path(__file__).resolve().parents[1]


def main():
    load_dotenv(ROOT / ".env")
    required = ("OPENAI_API_KEY", "PINECONE_API_KEY", "PINECONE_INDEX_NAME")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")
    paths = sorted(path for path in (ROOT / "ingestion/data").rglob("*")
                   if path.is_file() and path.suffix.lower() in {".pdf", ".docx"})
    if not paths:
        raise SystemExit("Add PDF or DOCX files to ingestion/data/ first.")
    store = PineconeVectorStore(
        index_name=os.environ["PINECONE_INDEX_NAME"],
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        namespace=os.getenv("PINECONE_NAMESPACE", "documents"),
    )
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    for path in paths:
        loader = PyPDFLoader(str(path)) if path.suffix.lower() == ".pdf" else Docx2txtLoader(str(path))
        chunks = splitter.split_documents(loader.load())
        ids = []
        for position, chunk in enumerate(chunks):
            chunk.metadata["source"] = path.relative_to(ROOT / "ingestion/data").as_posix()
            identity = f"{chunk.metadata['source']}:{position}:{chunk.page_content}"
            ids.append(hashlib.sha256(identity.encode()).hexdigest())
        if chunks:
            store.add_documents(chunks, ids=ids)
        print(f"Uploaded {len(chunks)} chunks from {path.name}")
    print("Ingestion complete. Replaced or removed documents require stale-vector cleanup.")


if __name__ == "__main__":
    main()
