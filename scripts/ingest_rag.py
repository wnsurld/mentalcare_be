from app.services.rag_ingest import ingest_tagged_docs
from pathlib import Path

if __name__ == "__main__":
    jsonl_path = Path("app/data/tagged/tagged_docs.jsonl")
    ingest_tagged_docs(jsonl_path)
