import os
import sys
from pathlib import Path
import glob

# Load dotenv to get API keys
from dotenv import load_dotenv
load_dotenv(override=True)

from src.models import Document
from src.chunking import RecursiveChunker
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from openai import OpenAI

def real_openai_llm(prompt: str) -> str:
    """Uses real OpenAI Chat Completion to answer."""
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful medical assistant. Answer only based on the provided context."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content

def setup_agent():
    print("Loading Vin Study domain documents...")
    all_paths = glob.glob("data/Vin Study*.md")
    # Chỉ lấy 2 file quan trọng nhất để indexing nhanh (vẫn đảm bảo đủ data trả lời câu hỏi mẫu)
    file_paths = [
        p for p in all_paths 
        if "Alpha+Thalassemia" in p or "Non_invasive_prenatal_testing" in p
    ]
    
    docs = []
    for raw_path in file_paths:
        path = Path(raw_path)
        content = path.read_text(encoding="utf-8")
        docs.append(Document(
            id=path.stem,
            content=content,
            metadata={"source": str(path), "extension": path.suffix.lower()}
        ))
        
    print("Applying RecursiveChunker(chunk_size=300)...")
    chunker = RecursiveChunker(chunk_size=300)
    chunked_docs = []
    for doc in docs:
        chunks = chunker.chunk(doc.content)
        for i, c in enumerate(chunks):
            chunked_docs.append(Document(
                id=f"{doc.id}_chunk_{i}",
                content=c,
                metadata=doc.metadata.copy()
            ))

    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "openai":
        try:
            embedder = OpenAIEmbedder()
        except Exception:
            embedder = _mock_embed
    else:
        embedder = _mock_embed
        
    print(f"Embedding backend active: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")
    
    print("\n[Indexing...]")
    store = EmbeddingStore(collection_name="interactive_store", embedding_fn=embedder)
    store.add_documents(chunked_docs)
    
    print(f"Stored {store.get_collection_size()} chunks in Database.\n")
    
    agent = KnowledgeBaseAgent(store=store, llm_fn=real_openai_llm)
    return agent

def run_interactive():
    agent = setup_agent()
    print("="*60)
    print("✅ HỆ THỐNG ĐÃ SẴN SÀNG! ĐANG DÙNG DỮ LIỆU MEDICAL (Vin Study)")
    print("Gõ 'exit' hoặc 'quit' để thoát.")
    print("="*60)
    
    while True:
        try:
            query = input("\n[Bạn hỏi] > ")
            if query.strip().lower() in ['exit', 'quit']:
                print("Tạm biệt!")
                break
            if not query.strip():
                continue
                
            print("\n[Agent đang suy nghĩ...]")
            response = agent.answer(query, top_k=3)
            print("="*40)
            print(f"[Agent trả lời]:\n{response}")
            print("="*40)
            
        except KeyboardInterrupt:
            print("\nTạm biệt!")
            break

if __name__ == "__main__":
    run_interactive()
