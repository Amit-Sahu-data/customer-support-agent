# knowledge_base/loader.py
# FAQ knowledge base with keyword search
# Reliable, fast, no external dependencies

import os
import json

FAQ_PATH = "./knowledge_base/faq.txt"
CHUNKS_PATH = "./knowledge_base/faq_chunks.json"

# Cache chunks in memory after first load
_CHUNKS_CACHE = []

def load_knowledge_base():
    global _CHUNKS_CACHE
    if _CHUNKS_CACHE:
        return _CHUNKS_CACHE

    if os.path.exists(CHUNKS_PATH):
        with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:
            _CHUNKS_CACHE = json.load(f)
        return _CHUNKS_CACHE

    with open(FAQ_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    chunks = [c.strip() for c in content.split('\n\n') if c.strip()]

    with open(CHUNKS_PATH, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    _CHUNKS_CACHE = chunks
    print(f"Knowledge base created with {len(chunks)} chunks!")
    return chunks

def search_faq(query: str, k: int = 3) -> str:
    """
    Keyword search over FAQ chunks.
    Reliable, fast, zero dependencies.
    Production upgrade path: swap with ChromaDB + embeddings.
    """
    chunks = load_knowledge_base()
    stopwords = {'i', 'my', 'the', 'a', 'an', 'is', 'it', 'to',
                 'do', 'how', 'what', 'can', 'will', 'was', 'are',
                 'for', 'in', 'of', 'and', 'you', 'your', 'me'}

    query_words = [w for w in query.lower().split()
                   if w not in stopwords]

    scored = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = sum(1 for w in query_words if w in chunk_lower)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(reverse=True)
    top = [c for _, c in scored[:k]]

    if not top:
        return "No relevant FAQ information found."

    return "\n\n---\n\n".join(top)

if __name__ == "__main__":
    print("Testing knowledge base...")
    result = search_faq("What is your return policy?")
    print(result[:300])
    print("\nKnowledge base working!")