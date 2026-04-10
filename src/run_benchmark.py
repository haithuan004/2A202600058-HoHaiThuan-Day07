import os
import glob
from pathlib import Path

# Adjust paths assuming this is run from the root of the project
import sys
sys.path.append(os.path.abspath("."))

from dotenv import load_dotenv
load_dotenv()

from src.models import Document
from src.chunking import FixedSizeChunker, SentenceChunker, RecursiveChunker, ChunkingStrategyComparator, compute_similarity
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent
from src.embeddings import OpenAIEmbedder
from main import demo_llm

embedder_fn = OpenAIEmbedder()

def load_documents(data_dir="data"):
    docs = []
    # Chỉ load các file bắt đầu bằng 'Vin Study' và mở rộng .md
    for file_path in glob.glob(f"{data_dir}/Vin Study*.md"):
        path = Path(file_path)
        content = path.read_text(encoding='utf-8')
        
        name_lower = path.name.lower()
        
        doc_type = "other"
        if "whitepaper" in name_lower: doc_type = "white_paper"
        elif "fact sheet" in name_lower or "factsheet" in name_lower or "fact_sheet" in name_lower: doc_type = "fact_sheet"
        elif "lecture" in name_lower: doc_type = "lecture"
        elif "guide" in name_lower: doc_type = "action_guide"
            
        topic = "general"
        if "thalassemia" in name_lower or "prenatal" in name_lower or "nipt" in name_lower or "genetics" in name_lower:
            topic = "genetics"
        elif "tumours" in name_lower or "cancer" in name_lower:
            topic = "oncology"
            
        source = "unknown"
        if "https_" in name_lower:
            parts = name_lower.split("https_")
            if len(parts) > 1:
                source = parts[1].split("_")[0]
            
        doc = Document(
            id=path.name,
            content=content,
            metadata={
                "doc_type": doc_type,
                "topic": topic,
                "source": source,
                "length": len(content)
            }
        )
        docs.append(doc)
    return docs

def do_baseline_comparison(docs):
    print("\n=== Baseline Analysis (Exercise 3.1) ===")
    sample_text = docs[0].content if docs else ""
    comparator = ChunkingStrategyComparator()
    results = comparator.compare(sample_text, chunk_size=300)
    
    for strategy, stats in results.items():
        print(f"Strategy: {strategy}")
        print(f"  Count: {stats['count']}")
        print(f"  Avg Length: {stats['avg_length']:.2f}")
    
def do_similarity_predictions():
    print("\n=== Similarity Predictions (Exercise 3.3) ===")
    pairs = [
        ("Alpha-thalassemia is an inherited blood disorder.", "It is passed down from parents to children through genes.", "high (Semantic match)"),
        ("Alpha-thalassemia is an inherited blood disorder.", "Chemotherapy is used to destroy cancer cells.", "low (Unrelated context)"),
        ("NIPT tests for Down syndrome.", "Trisomy 21 is a chromosome condition.", "high (Concept overlap)"),
        ("Brain tumours are the most common tumours.", "Astrocytoma is a type of tumour.", "high (Sub-category overlap)"),
        ("Iron chelation therapy prevents iron overload.", "Intrauterine blood transfusions are performed before birth.", "medium (Different treatments)")
    ]
    for i, (a, b, pred) in enumerate(pairs, 1):
        vec_a = embedder_fn(a)
        vec_b = embedder_fn(b)
        score = compute_similarity(vec_a, vec_b)
        print(f"Pair {i}:")
        print(f"  A: {a}")
        print(f"  B: {b}")
        print(f"  Prediction: {pred} | Actual Score: {score:.4f}")

def run_benchmark(docs):
    print("\n=== Running Benchmark Queries (Exercise 3.4) ===")
    chunker = RecursiveChunker(chunk_size=300)
    
    chunked_docs = []
    for doc in docs:
        chunks = chunker.chunk(doc.content)
        for i, c in enumerate(chunks):
            chunk_doc = Document(
                id=f"{doc.id}_chunk_{i}",
                content=c,
                metadata=doc.metadata.copy()
            )
            chunked_docs.append(chunk_doc)
            
    store = EmbeddingStore(collection_name="benchmark_medical", embedding_fn=embedder_fn)
    store.add_documents(chunked_docs)
    
    agent = KnowledgeBaseAgent(store, demo_llm)
    
    import re
    with open("benchmark_queries.md", "r", encoding="utf-8") as f:
        content = f.read()
    queries = re.findall(r"\*\*Question:\*\* (.*?)\n", content)
    
    for i, q in enumerate(queries, 1):
        print(f"\n" + "="*50)
        print(f"Query {i}: {q}")
        results = store.search(q, top_k=3)
        if results:
            print(f"  Top-1 Score: {results[0].get('score', 0):.4f}")
            print(f"  Top-1 Source: doc_type={results[0]['metadata'].get('doc_type', '')}, topic={results[0]['metadata'].get('topic', '')}")
            print(f"  Top-1 ID: {results[0]['id']}")
            print(f"  Top-1 Preview: {results[0]['content'][:100].replace(chr(10), ' ')}...")
        
        answer = agent.answer(q, top_k=3)
        print(f"  Agent action: {answer}")

if __name__ == "__main__":
    print("Loading ONLY 'Vin Study' documents from data/ ...")
    docs = load_documents("data")
    print(f"Loaded {len(docs)} documents.")
    
    if docs:
        do_baseline_comparison(docs)
        do_similarity_predictions()
        run_benchmark(docs)
    else:
        print("No 'Vin Study' documents found.")
    print("\nAll tasks completed successfully. Review output to fill REPORT.md")
