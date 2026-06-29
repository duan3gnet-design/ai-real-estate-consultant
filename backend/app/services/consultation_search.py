"""
Consultation Search Service
===========================
Vector store RIÊNG cho dữ liệu buổi tư vấn — tách biệt với BĐS index.

Mỗi "document" trong vector store là một CHUNK của transcript hoặc
một SESSION summary (metadata CRM), cho phép tìm các case tương tự
theo ngữ nghĩa câu hỏi của khách hàng.
"""

import re
import json
import threading
from typing import Optional
from pathlib import Path

from app.database import get_connection, DB_PATH

_consult_collection = None
_embed_model = None          # share với properties search nếu đã load
_lock = threading.Lock()

CHROMA_DIR = DB_PATH.parent / "chroma"
EMBED_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def _get_collection():
    global _consult_collection, _embed_model
    with _lock:
        if _consult_collection is not None:
            return _consult_collection, _embed_model
        try:
            import chromadb
            from chromadb.config import Settings
            from sentence_transformers import SentenceTransformer

            # Reuse model nếu properties search đã load
            from app.services import search as prop_search
            if prop_search._embed_model is not None:
                _embed_model = prop_search._embed_model
            else:
                print("[ConsultSearch] Loading embedding model...")
                _embed_model = SentenceTransformer(EMBED_MODEL_NAME)

            CHROMA_DIR.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(
                path=str(CHROMA_DIR),
                settings=Settings(anonymized_telemetry=False),
            )
            _consult_collection = client.get_or_create_collection(
                name="consultations",
                metadata={"hnsw:space": "cosine"},
            )
            print(f"[ConsultSearch] Ready. Collection size: {_consult_collection.count()}")
            return _consult_collection, _embed_model
        except ImportError as e:
            print(f"[ConsultSearch] DISABLED – {e}")
            return None, None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _session_to_text(session: dict) -> str:
    """Tạo văn bản đại diện cho một session (dùng để embed)."""
    parts = []
    if session.get("loai_nhu_cau"):
        parts.append(f"Nhu cầu: {session['loai_nhu_cau']}")
    if session.get("loai_bds_quan_tam"):
        parts.append(f"Loại BĐS: {session['loai_bds_quan_tam']}")
    if session.get("khu_vuc_quan_tam"):
        parts.append(f"Khu vực: {session['khu_vuc_quan_tam']}")
    if session.get("ngan_sach_min") or session.get("ngan_sach_max"):
        ng_min = session.get("ngan_sach_min", "")
        ng_max = session.get("ngan_sach_max", "")
        parts.append(f"Ngân sách: {ng_min}–{ng_max} triệu")
    if session.get("tieu_chi_khac"):
        parts.append(session["tieu_chi_khac"])
    if session.get("ket_qua"):
        parts.append(f"Kết quả: {session['ket_qua']}")
    if session.get("ly_do_tu_choi"):
        parts.append(f"Lý do từ chối: {session['ly_do_tu_choi']}")
    if session.get("ghi_chu"):
        parts.append(session["ghi_chu"][:300])
    return " | ".join(p for p in parts if p)


def _chunk_to_text(chunk: dict) -> str:
    speaker = chunk.get("speaker", "unknown")
    content = chunk.get("content", "")
    topics = chunk.get("topics", "")
    return f"[{speaker}] {content} | chủ đề: {topics}"


# ─── Index functions ──────────────────────────────────────────────────────────

def index_session(session: dict):
    """Index 1 session (metadata CRM) vào vector store."""
    col, model = _get_collection()
    if col is None:
        return
    text = _session_to_text(session)
    if not text.strip():
        return
    embedding = model.encode(text).tolist()
    col.upsert(
        ids=[f"session_{session['id']}"],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{
            "type": "session",
            "session_id": session["id"],
            "ket_qua": session.get("ket_qua") or "",
            "loai_nhu_cau": session.get("loai_nhu_cau") or "",
        }],
    )


def index_chunk(chunk: dict):
    """Index 1 transcript chunk vào vector store."""
    col, model = _get_collection()
    if col is None:
        return
    text = _chunk_to_text(chunk)
    embedding = model.encode(text).tolist()
    col.upsert(
        ids=[f"chunk_{chunk['id']}"],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{
            "type": "chunk",
            "chunk_id": chunk["id"],
            "session_id": chunk["session_id"],
            "speaker": chunk.get("speaker") or "unknown",
        }],
    )


def index_chunks_batch(chunks: list[dict], batch_size: int = 500):
    col, model = _get_collection()
    if col is None or not chunks:
        return
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        ids = [f"chunk_{c['id']}" for c in batch]
        texts = [_chunk_to_text(c) for c in batch]
        embeddings = model.encode(texts, batch_size=64, show_progress_bar=False).tolist()
        metadatas = [{
            "type": "chunk",
            "chunk_id": c["id"],
            "session_id": c["session_id"],
            "speaker": c.get("speaker") or "unknown",
        } for c in batch]
        col.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    print(f"[ConsultSearch] Indexed {len(chunks)} chunks.")


def index_sessions_batch(sessions: list[dict], batch_size: int = 500):
    col, model = _get_collection()
    if col is None or not sessions:
        return
    for i in range(0, len(sessions), batch_size):
        batch = sessions[i: i + batch_size]
        ids = [f"session_{s['id']}" for s in batch]
        texts = [_session_to_text(s) for s in batch]
        embeddings = model.encode(texts, batch_size=64, show_progress_bar=False).tolist()
        metadatas = [{
            "type": "session",
            "session_id": s["id"],
            "ket_qua": s.get("ket_qua") or "",
            "loai_nhu_cau": s.get("loai_nhu_cau") or "",
        } for s in batch]
        col.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    print(f"[ConsultSearch] Indexed {len(sessions)} sessions.")


def delete_session_from_index(session_id: int):
    col, _ = _get_collection()
    if col:
        try:
            col.delete(where={"session_id": session_id})
        except Exception:
            pass


# ─── Search functions ─────────────────────────────────────────────────────────

def _fts_build_query(q: str) -> str:
    tokens = re.findall(r'\w+', q, re.UNICODE)
    return " ".join(f'"{t}"*' for t in tokens) if tokens else '""'


def fts_search_consultations(query: str, top_k: int = 20, ket_qua: str = None) -> list[dict]:
    """Full-text search transcript_chunks + filter theo kết quả session."""
    conn = get_connection()
    try:
        params = []
        if query.strip():
            fq = _fts_build_query(query)
            sql = """
                SELECT tc.*, cs.ket_qua, cs.loai_nhu_cau, cs.khu_vuc_quan_tam,
                       cs.ngan_sach_min, cs.ngan_sach_max, cs.nguoi_tu_van,
                       fts.rank AS fts_rank
                FROM transcript_fts fts
                JOIN transcript_chunks tc ON tc.id = fts.id
                JOIN consultation_sessions cs ON cs.id = tc.session_id
                WHERE transcript_fts MATCH ?
            """
            params.append(fq)
        else:
            sql = """
                SELECT tc.*, cs.ket_qua, cs.loai_nhu_cau, cs.khu_vuc_quan_tam,
                       cs.ngan_sach_min, cs.ngan_sach_max, cs.nguoi_tu_van, 0 AS fts_rank
                FROM transcript_chunks tc
                JOIN consultation_sessions cs ON cs.id = tc.session_id
                WHERE 1=1
            """
        if ket_qua:
            sql += " AND cs.ket_qua = ?"
            params.append(ket_qua)
        sql += " ORDER BY fts_rank LIMIT ?"
        params.append(top_k)
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[FTS Consult] Error: {e}")
        return []
    finally:
        conn.close()


def vector_search_consultations(query: str, top_k: int = 20, doc_type: str = None) -> list[dict]:
    """Vector search trên consultation collection."""
    col, model = _get_collection()
    if col is None or col.count() == 0:
        return []
    try:
        embedding = model.encode(query).tolist()
        where = {"type": doc_type} if doc_type else None
        results = col.query(
            query_embeddings=[embedding],
            n_results=min(top_k, col.count()),
            include=["metadatas", "distances", "documents"],
            where=where,
        )
        out = []
        for meta, dist, doc in zip(
            results["metadatas"][0],
            results["distances"][0],
            results["documents"][0],
        ):
            out.append({**meta, "_dist": dist, "_doc": doc})
        return out
    except Exception as e:
        print(f"[Vector Consult] Error: {e}")
        return []


def hybrid_search_consultations(
    query: str,
    top_k: int = 10,
    rrf_k: int = 60,
    ket_qua_filter: str = None,
) -> tuple[list[dict], list[dict]]:
    """
    Hybrid search trên lịch sử tư vấn.
    Trả về (similar_chunks, similar_sessions) — 2 loại context khác nhau.
    """
    # FTS trên transcript chunks
    fts_chunks = fts_search_consultations(query, top_k=top_k * 2, ket_qua=ket_qua_filter)
    # Vector trên chunks + sessions
    vec_chunks = vector_search_consultations(query, top_k=top_k * 2, doc_type="chunk")
    vec_sessions = vector_search_consultations(query, top_k=top_k, doc_type="session")

    # RRF merge chunks
    scores: dict = {}
    chunk_data: dict = {}

    for rank, c in enumerate(fts_chunks):
        key = f"c_{c['id']}"
        scores[key] = scores.get(key, 0) + 1.0 / (rrf_k + rank + 1)
        chunk_data[key] = c

    for rank, c in enumerate(vec_chunks):
        cid = c.get("chunk_id")
        if cid:
            key = f"c_{cid}"
            scores[key] = scores.get(key, 0) + 1.0 / (rrf_k + rank + 1)
            if key not in chunk_data:
                chunk_data[key] = c

    top_chunks_keys = sorted(scores, key=lambda x: scores[x], reverse=True)[:top_k]
    top_chunks = [chunk_data[k] for k in top_chunks_keys if k in chunk_data]

    # Lấy thêm session metadata cho các session liên quan
    session_ids = list({c.get("session_id") for c in top_chunks if c.get("session_id")})
    sessions = []
    if session_ids:
        conn = get_connection()
        placeholders = ",".join("?" * len(session_ids))
        rows = conn.execute(
            f"SELECT * FROM consultation_sessions WHERE id IN ({placeholders})",
            session_ids,
        ).fetchall()
        conn.close()
        sessions = [dict(r) for r in rows]

    # Merge sessions từ vector search
    vec_session_ids = {s.get("session_id") for s in vec_sessions if s.get("session_id")}
    extra_ids = vec_session_ids - set(session_ids)
    if extra_ids:
        conn = get_connection()
        placeholders = ",".join("?" * len(extra_ids))
        rows = conn.execute(
            f"SELECT * FROM consultation_sessions WHERE id IN ({placeholders})",
            list(extra_ids),
        ).fetchall()
        conn.close()
        sessions.extend([dict(r) for r in rows])

    return top_chunks[:top_k], sessions[:top_k]


# ─── Format context cho prompt ────────────────────────────────────────────────

def format_consultation_context(chunks: list[dict], sessions: list[dict]) -> str:
    """Tạo context từ lịch sử tư vấn để inject vào system prompt."""
    if not chunks and not sessions:
        return ""

    lines = ["## KINH NGHIỆM TỪ CÁC BUỔI TƯ VẤN TRƯỚC (dữ liệu công ty)\n"]

    # Group chunks theo session
    session_chunks: dict[int, list] = {}
    for c in chunks:
        sid = c.get("session_id", 0)
        session_chunks.setdefault(sid, []).append(c)

    # Lấy session metadata
    session_map = {s["id"]: s for s in sessions}

    shown = 0
    for sid, schunks in session_chunks.items():
        if shown >= 5:
            break
        sess = session_map.get(sid, {})
        ket_qua = sess.get("ket_qua", "?")
        loai = sess.get("loai_nhu_cau", "")
        khu_vuc = sess.get("khu_vuc_quan_tam", "")
        ng_min = sess.get("ngan_sach_min")
        ng_max = sess.get("ngan_sach_max")
        ngan_sach = f"{ng_min}–{ng_max} triệu" if (ng_min or ng_max) else ""

        header = f"### Case #{sid}"
        meta = []
        if loai:     meta.append(loai)
        if khu_vuc:  meta.append(khu_vuc)
        if ngan_sach: meta.append(ngan_sach)
        meta.append(f"→ **{ket_qua}**")
        lines.append(f"{header} | {' | '.join(meta)}")

        for c in schunks[:4]:
            speaker_label = "Tư vấn viên" if c.get("speaker") == "consultant" else "Khách hàng"
            content = c.get("content", "").strip()
            if content:
                lines.append(f"> [{speaker_label}]: {content[:200]}")

        lines.append("")
        shown += 1

    # Sessions không có chunk (từ vector search thuần)
    for sess in sessions:
        if sess["id"] in session_chunks:
            continue
        if shown >= 8:
            break
        ket_qua = sess.get("ket_qua", "?")
        ly_do = sess.get("ly_do_tu_choi", "")
        ghi_chu = sess.get("ghi_chu", "")
        lines.append(
            f"### Case #{sess['id']} | {sess.get('loai_nhu_cau','')} "
            f"| {sess.get('khu_vuc_quan_tam','')} → **{ket_qua}**"
        )
        if ly_do:
            lines.append(f"> Lý do từ chối: {ly_do[:150]}")
        if ghi_chu:
            lines.append(f"> Ghi chú: {ghi_chu[:150]}")
        lines.append("")
        shown += 1

    if shown == 0:
        return ""

    lines.append(
        "_Hãy học từ các case trên: sử dụng cách tiếp cận hiệu quả, tránh lỗi đã gặp._"
    )
    return "\n".join(lines)
