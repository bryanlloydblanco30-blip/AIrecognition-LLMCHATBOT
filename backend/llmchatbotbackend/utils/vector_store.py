import faiss
import numpy as np
import json
import os
from sentence_transformers import SentenceTransformer

# Resolve data paths relative to THIS file so they work no matter what CWD is used
_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_HERE, "..", "data")

INDEX_PATH = os.path.join(_DATA_DIR, "vector_index.faiss")
DOCS_PATH  = os.path.join(_DATA_DIR, "documents.json")

model = SentenceTransformer('all-MiniLM-L6-v2')

def save_index(index, documents):
    if not os.path.exists("data"):
        os.makedirs("data")
    faiss.write_index(index, INDEX_PATH)
    with open(DOCS_PATH, "w") as f:
        json.dump(documents, f)
    print(f"Index and documents saved to {INDEX_PATH}")

def load_index():
    if os.path.exists(INDEX_PATH) and os.path.exists(DOCS_PATH):
        try:
            index = faiss.read_index(INDEX_PATH)
            with open(DOCS_PATH, "r") as f:
                documents = json.load(f)
            print(f"Loaded existing index with {len(documents)} documents.")
            return index, documents
        except Exception as e:
            print(f"Error loading index: {e}")
    return None, []

def create_index(documents):
    print(f"Indexing {len(documents)} documents...")
    embeddings = model.encode(documents, show_progress_bar=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype('float32'))
    return index

def search_index(index, documents, query, k=3):
    if index is None or not documents:
        return ""
    
    query_embedding = model.encode([query])
    D, I = index.search(np.array(query_embedding).astype('float32'), k=k)
    
    relevant_docs = [documents[i] for i in I[0] if i < len(documents)]
    return "\n".join(relevant_docs)
