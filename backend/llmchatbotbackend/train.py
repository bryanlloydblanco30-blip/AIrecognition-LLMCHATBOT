import json
import os
import sys

# Ensure local utils folder is loaded
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.vector_store import create_index, save_index

def train_rag():
    docs_path = os.path.join("data", "documents.json")
    if not os.path.exists(docs_path):
        print(f"❌ Error: {docs_path} not found. Make sure data/documents.json is populated.")
        return
    
    with open(docs_path, "r", encoding="utf-8") as f:
        documents = json.load(f)
        
    print(f"📖 Loaded {len(documents)} text entries from dataset...")
    index = create_index(documents)
    save_index(index, documents)
    print("⚡ FAISS vector index successfully built and saved to data/vector_index.faiss!")

if __name__ == "__main__":
    train_rag()
