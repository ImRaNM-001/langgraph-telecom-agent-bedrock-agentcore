from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from src.config import params, get_csv_path
from src.data_loader import load_faq_csv
from src.logging import logger

_faq_store = None


def get_faq_store() -> FAISS:
    """Lazily build (once) the FAISS vector store over the Lauki Phones FAQ dataset."""
    global _faq_store
    if _faq_store is None:
        docs = load_faq_csv(get_csv_path())
        emb = HuggingFaceEmbeddings(
            model_name=params.knowledge_base.embedding_model,
        )
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=params.knowledge_base.chunk_size,
            chunk_overlap=params.knowledge_base.chunk_overlap,
        )
        chunks = splitter.split_documents(docs)
        logger.info(f"Building FAISS index over {len(chunks)} chunks")
        _faq_store = FAISS.from_documents(chunks, emb)
    return _faq_store
