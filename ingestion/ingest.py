"""Upload local PDF, DOCX, and UTF-8 TXT documents to Pinecone."""

import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

ROOT = Path(__file__).resolve().parents[1]


def load_documents(path: Path) -> list[Document]:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        return [Document(page_content=page.extract_text() or "", metadata={"page": number})
                for number, page in enumerate(PdfReader(str(path)).pages)]
    if path.suffix.lower() == ".docx":
        import docx2txt

        return [Document(page_content=docx2txt.process(str(path)))]
    return [Document(page_content=path.read_text(encoding="utf-8-sig"))]


def main():
    load_dotenv(ROOT / ".env")
    required = ("OPENAI_API_KEY", "PINECONE_API_KEY", "PINECONE_INDEX_NAME")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")
    paths = sorted(path for path in (ROOT / "ingestion/data").rglob("*")
                   if path.is_file() and path.suffix.lower() in {".pdf", ".docx", ".txt"})
    if not paths:
        raise SystemExit("Add PDF, DOCX, or UTF-8 TXT files to ingestion/data/ first.")
    store = PineconeVectorStore(
        index_name=os.environ["PINECONE_INDEX_NAME"],
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        namespace=os.getenv("PINECONE_NAMESPACE", "documents"),
    )
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    for path in paths:
        chunks = splitter.split_documents(load_documents(path))
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
