"""Module 2/4 — Knowledge Base Agent (RAG)"""
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from core.config import CHROMA_DIR
from core.llm import llm, get_text_content

os.makedirs(CHROMA_DIR, exist_ok=True)
_embeddings = None
_vectorstore = None
def get_vectorstore():
    global _embeddings,_vectorstore
    if _vectorstore is None:
        _embeddings=HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MinLM-L6-v2"
        )
        _vectorstore=Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings,
        )
    return _vectorstore

def build_knowledge_base(file_paths: list[str]) -> str:
    """Load PDFs/TXT files from disk paths and add them to the vector store."""
    docs = []
    for path in file_paths:
        if path.lower().endswith(".pdf"):
            docs.extend(PyPDFLoader(path).load())
        elif path.lower().endswith(".txt"):
            docs.extend(TextLoader(path).load())

    if not docs:
        return "No supported files found (only .pdf and .txt are supported)."

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    _vectorstore.add_documents(chunks)
    return f"Added {len(chunks)} chunks from {len(file_paths)} file(s) to the knowledge base."


def search_knowledge_base(query: str) -> str:
    """Answer a question using only the uploaded documents."""
    retriever = _vectorstore.as_retriever(search_kwargs={"k": 4})
    relevant = retriever.invoke(query)
    if not relevant:
        return "Nothing relevant found in the knowledge base yet. Upload documents first."
    context = "\n\n".join(d.page_content for d in relevant)
    prompt = f"Answer using ONLY this context. If the answer isn't in it, say so.\n\nContext:\n{context}\n\nQuestion: {query}"
    return get_text_content(llm.invoke(prompt))
