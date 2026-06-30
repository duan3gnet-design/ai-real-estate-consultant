"""
Consultation Search Service — Elasticsearch
=============================================
Hai index riêng: consultation_sessions (metadata CRM) và transcript_chunks
(từng đoạn hội thoại), cho phép tìm case tương tự theo ngữ nghĩa.
"""
from typing import Optional

from app.es_client import get_es, IDX_SESSIONS, IDX_CHUNKS
from app.embedding import embed_text, embed_texts


def _session_to_text(session: dict) -> str:
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
    es = get_es()
    text = _session_to_text(session)
    doc = {k: v for k, v in session.items() if v is not None}
    if text.strip():
        doc["embedding"] = embed_text(text)
    es.index(index=IDX_SESSIONS, id=str(session["id"]), document=doc)


def index_sessions_batch(sessions: list[dict], batch_size: int = 500):
    from elasticsearch.helpers import bulk
    es = get_es()
    if not sessions:
        return

    for i in range(0, len(sessions), batch_size):
        batch = sessions[i: i + batch_size]
        texts = [_session_to_text(s) for s in batch]
        embeddings = embed_texts(texts, batch_size=64)

        actions = []
        for s, emb in zip(batch, embeddings):
            doc = {k: v for k, v in s.items() if v is not None}
            doc["embedding"] = emb
            actions.append({"_index": IDX_SESSIONS, "_id": str(s["id"]), "_source": doc})
        bulk(es, actions)

    es.indices.refresh(index=IDX_SESSIONS)
    print(f"[ConsultSearch] Indexed {len(sessions)} sessions.")


def index_chunk(chunk: dict):
    es = get_es()
    text = _chunk_to_text(chunk)
    doc = {k: v for k, v in chunk.items() if v is not None}
    doc["embedding"] = embed_text(text)
    es.index(index=IDX_CHUNKS, id=str(chunk["id"]), document=doc)


def index_chunks_batch(chunks: list[dict], batch_size: int = 500):
    from elasticsearch.helpers import bulk
    es = get_es()
    if not chunks:
        return

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        texts = [_chunk_to_text(c) for c in batch]
        embeddings = embed_texts(texts, batch_size=64)

        actions = []
        for c, emb in zip(batch, embeddings):
            doc = {k: v for k, v in c.items() if v is not None}
            doc["embedding"] = emb
            actions.append({"_index": IDX_CHUNKS, "_id": str(c["id"]), "_source": doc})
        bulk(es, actions)

    es.indices.refresh(index=IDX_CHUNKS)
    print(f"[ConsultSearch] Indexed {len(chunks)} chunks.")


def delete_session_from_index(session_id: int):
    es = get_es()
    try:
        es.delete(index=IDX_SESSIONS, id=str(session_id))
    except Exception:
        pass
    try:
        es.delete_by_query(
            index=IDX_CHUNKS,
            query={"term": {"session_id": session_id}},
        )
    except Exception:
        pass


def delete_chunks_for_session(session_id: int):
    es = get_es()
    try:
        es.delete_by_query(
            index=IDX_CHUNKS,
            query={"term": {"session_id": session_id}},
        )
    except Exception:
        pass


# ─── Search functions ─────────────────────────────────────────────────────────

def fts_search_consultations(query: str, top_k: int = 20, ket_qua: str = None) -> list[dict]:
    """Full-text search trên transcript_chunks."""
    es = get_es()
    filt = []
    if ket_qua:
        filt.append({"term": {"_ket_qua": ket_qua}})  # placeholder, join thủ công bên dưới

    body_query = {"bool": {"filter": []}}
    if query.strip():
        body_query["bool"]["must"] = [{"match": {"content": query}}]
    else:
        body_query["bool"]["must"] = [{"match_all": {}}]

    try:
        resp = es.search(index=IDX_CHUNKS, query=body_query, size=top_k)
        chunks = [hit["_source"] for hit in resp["hits"]["hits"]]
    except Exception as e:
        print(f"[FTS Consult] Error: {e}")
        return []

    if not chunks:
        return chunks

    # Join thêm metadata session
    session_ids = list({c.get("session_id") for c in chunks if c.get("session_id")})
    session_map = _fetch_sessions_by_ids(session_ids)

    out = []
    for c in chunks:
        sess = session_map.get(c.get("session_id"), {})
        if ket_qua and sess.get("ket_qua") != ket_qua:
            continue
        merged = {**c}
        merged["ket_qua"] = sess.get("ket_qua")
        merged["loai_nhu_cau"] = sess.get("loai_nhu_cau")
        merged["khu_vuc_quan_tam"] = sess.get("khu_vuc_quan_tam")
        merged["ngan_sach_min"] = sess.get("ngan_sach_min")
        merged["ngan_sach_max"] = sess.get("ngan_sach_max")
        merged["nguoi_tu_van"] = sess.get("nguoi_tu_van")
        out.append(merged)
    return out


def vector_search_consultations(query: str, top_k: int = 20, doc_type: str = "chunk") -> list[dict]:
    """Vector kNN search trên chunk hoặc session collection."""
    es = get_es()
    embedding = embed_text(query)
    index_name = IDX_CHUNKS if doc_type == "chunk" else IDX_SESSIONS

    knn = {
        "field": "embedding",
        "query_vector": embedding,
        "k": top_k,
        "num_candidates": max(top_k * 4, 100),
    }

    try:
        resp = es.search(index=index_name, knn=knn, size=top_k)
        out = []
        for hit in resp["hits"]["hits"]:
            src = hit["_source"]
            if doc_type == "chunk":
                out.append({**src, "chunk_id": src.get("id"), "_dist": 1 - hit["_score"]})
            else:
                out.append({**src, "session_id": src.get("id"), "_dist": 1 - hit["_score"]})
        return out
    except Exception as e:
        print(f"[Vector Consult] Error: {e}")
        return []


def _fetch_sessions_by_ids(session_ids: list[int]) -> dict[int, dict]:
    if not session_ids:
        return {}
    es = get_es()
    try:
        resp = es.search(
            index=IDX_SESSIONS,
            query={"terms": {"id": session_ids}},
            size=len(session_ids),
        )
        return {hit["_source"]["id"]: hit["_source"] for hit in resp["hits"]["hits"]}
    except Exception:
        return {}


def hybrid_search_consultations(
    query: str,
    top_k: int = 10,
    rrf_k: int = 60,
    ket_qua_filter: str = None,
) -> tuple[list[dict], list[dict]]:
    """Hybrid search trên lịch sử tư vấn. Trả về (chunks, sessions)."""
    fts_chunks = fts_search_consultations(query, top_k=top_k * 2, ket_qua=ket_qua_filter)
    vec_chunks = vector_search_consultations(query, top_k=top_k * 2, doc_type="chunk")
    vec_sessions = vector_search_consultations(query, top_k=top_k, doc_type="session")

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
            chunk_data.setdefault(key, c)

    top_chunks_keys = sorted(scores, key=lambda x: scores[x], reverse=True)[:top_k]
    top_chunks = [chunk_data[k] for k in top_chunks_keys if k in chunk_data]

    session_ids = list({c.get("session_id") for c in top_chunks if c.get("session_id")})
    session_map = _fetch_sessions_by_ids(session_ids)
    sessions = list(session_map.values())

    vec_session_ids = {s.get("session_id") for s in vec_sessions if s.get("session_id")}
    extra_ids = vec_session_ids - set(session_ids)
    if extra_ids:
        extra_map = _fetch_sessions_by_ids(list(extra_ids))
        sessions.extend(extra_map.values())

    return top_chunks[:top_k], sessions[:top_k]


# ─── Format context cho prompt ────────────────────────────────────────────────

def format_consultation_context(chunks: list[dict], sessions: list[dict]) -> str:
    if not chunks and not sessions:
        return ""

    lines = ["## KINH NGHIỆM TỪ CÁC BUỔI TƯ VẤN TRƯỚC (dữ liệu công ty)\n"]

    session_chunks: dict[int, list] = {}
    for c in chunks:
        sid = c.get("session_id", 0)
        session_chunks.setdefault(sid, []).append(c)

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
        if loai: meta.append(loai)
        if khu_vuc: meta.append(khu_vuc)
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

    lines.append("_Hãy học từ các case trên: sử dụng cách tiếp cận hiệu quả, tránh lỗi đã gặp._")
    return "\n".join(lines)
