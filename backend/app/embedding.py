"""
Embedding Service — Singleton SentenceTransformer model
=========================================================
Dùng chung cho cả properties và consultations index vào Elasticsearch
(dense_vector field). Tách riêng để tránh load model 2 lần.
"""
import threading

_model = None
_lock = threading.Lock()

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # hỗ trợ tiếng Việt, 384 dims


def get_embedder():
    global _model
    with _lock:
        if _model is None:
            from sentence_transformers import SentenceTransformer
            print(f"[Embedding] Loading model {MODEL_NAME}...")
            _model = SentenceTransformer(MODEL_NAME)
            print("[Embedding] Model ready.")
        return _model


def embed_text(text: str) -> list[float]:
    model = get_embedder()
    return model.encode(text).tolist()


def embed_texts(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    model = get_embedder()
    return model.encode(texts, batch_size=batch_size, show_progress_bar=False).tolist()
