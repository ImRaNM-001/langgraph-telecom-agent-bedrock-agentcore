import csv
from typing import List
from pathlib import Path

from langchain_core.documents import Document

from src.logging import logger


def load_faq_csv(path: Path) -> List[Document]:
    """Load the Lauki Phones Q&A dataset into LangChain Documents."""
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = row["question"].strip()
            a = row["answer"].strip()
            docs.append(Document(page_content=f"Q: {q}\nA: {a}"))
    logger.info(f"Loaded {len(docs)} FAQ entries from {path}")
    return docs
