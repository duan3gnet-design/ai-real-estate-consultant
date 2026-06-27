"""
Hybrid Search Service
=====================
Kết hợp 2 phương pháp:
1. Vector Search  – ChromaDB + sentence-transformers (tìm ngữ nghĩa)
2. Full-text + Filter – SQLite FTS5 + structured filters (tìm chính xác)

Kết quả được merge theo thuật toán Reciprocal Rank Fusion (RRF),
trả về top-K BĐS phù hợp nhất để inject vào prompt AI.
"""

import re
import sqlite3
import threading
from typing import Optional
from pathlib import Path

from app.database import get_connection, DB_PATH

# ChromaDB + embeddings (lazy import để không chặn startup)
_chroma_client = None
_chroma_collection = None
_embed_model = None
_chroma_lock = threading.Lock()

CHROMA_DIR = DB_PATH.parent / "chroma"
EMBED_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # hỗ trợ tiếng Việt, nhẹ ~120MB


def _get_chroma():
    """Lazy-load ChromaDB và embedding model (lần đầu mất ~5-10s)."""
    global _chroma_client, _chroma_collection, _embed_model
    with _chroma_lock:
        if _chroma_collection is not None:
            return _chroma_collection, _embed_model

        try:
            import chromadb
            from chromadb.config import Settings
            from sentence_transformers import SentenceTransformer

            print("[VectorSearch] Loading embedding model...")
            _embed_model = SentenceTransformer(EMBED_MODEL_NAME)

            CHROMA_DIR.mkdir(parents=True, exist_ok=True)
            _chroma_client = chromadb.PersistentClient(
                path=str(CHROMA_DIR),
                settings=Settings(anonymized_telemetry=False),
            )
            _chroma_collection = _chroma_client.get_or_create_collection(
                name="properties",
                metadata={"hnsw:space": "cosine"},
            )
            print(f"[VectorSearch] Ready. Collection size: {_chroma_collection.count()}")
            return _chroma_collection, _embed_model

        except ImportError as e:
            print(f"[VectorSearch] DISABLED – missing package: {e}")
            return None, None


def _row_to_text(row: dict) -> str:
    """Chuyển một BĐS thành đoạn văn bản để embed."""
    parts = [
        row.get("ten", ""),
        row.get("loai", ""),
        row.get("trang_thai", ""),
        row.get("dia_chi", ""),
        row.get("phuong_xa") or "",
        row.get("quan_huyen") or "",
        row.get("tinh_thanh", ""),
    ]
    if row.get("dien_tich_san"):
        parts.append(f"diện tích {row['dien_tich_san']} m2")
    if row.get("dien_tich_dat"):
        parts.append(f"đất {row['dien_tich_dat']} m2")
    if row.get("so_phong_ngu"):
        parts.append(f"{row['so_phong_ngu']} phòng ngủ")
    if row.get("gia_ban"):
        parts.append(f"giá bán {row['gia_ban']} triệu")
    if row.get("gia_thue"):
        parts.append(f"giá thuê {row['gia_thue']} triệu tháng")
    if row.get("phap_ly"):
        parts.append(row["phap_ly"])
    if row.get("tien_ich"):
        parts.append(row["tien_ich"])
    if row.get("mo_ta"):
        parts.append(row["mo_ta"][:300])
    return " | ".join(p for p in parts if p.strip())


def index_property(prop_id: int, row: dict):
    """Thêm/cập nhật 1 BĐS vào vector store."""
    col, model = _get_chroma()
    if col is None:
        return
    text = _row_to_text(row)
    embedding = model.encode(text).tolist()
    col.upsert(
        ids=[str(prop_id)],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{"id": prop_id}],
    )


def index_properties_batch(rows: list[dict], batch_size: int = 500):
    """Bulk index nhiều BĐS (dùng khi import)."""
    col, model = _get_chroma()
    if col is None:
        return
    for i in range(0, len(rows), batch_size):
        batch = rows[i: i + batch_size]
        ids = [str(r["id"]) for r in batch]
        texts = [_row_to_text(r) for r in batch]
        embeddings = model.encode(texts, batch_size=64, show_progress_bar=False).tolist()
        metadatas = [{"id": r["id"]} for r in batch]
        col.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    print(f"[VectorSearch] Indexed {len(rows)} properties.")


def delete_from_index(prop_id: int):
    col, _ = _get_chroma()
    if col:
        try:
            col.delete(ids=[str(prop_id)])
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Full-text + structured filter search (SQLite FTS5)
# ---------------------------------------------------------------------------

def _build_fts_query(query: str) -> str:
    """Chuẩn hóa query thành FTS5 match expression."""
    tokens = re.findall(r'\w+', query, re.UNICODE)
    if not tokens:
        return '""'
    # Mỗi token tìm prefix match, tất cả phải xuất hiện (AND mặc định FTS5)
    return " ".join(f'"{t}"*' for t in tokens)


def fts_search(
    query: str,
    filters: Optional[dict] = None,
    top_k: int = 30,
    conn: Optional[sqlite3.Connection] = None,
) -> list[dict]:
    """
    Full-text search + structured filter trên SQLite.
    filters: dict với các key = tên cột, value = giá trị hoặc (min, max).
    """
    close_after = conn is None
    if conn is None:
        conn = get_connection()

    try:
        params = []
        conditions = []

        # FTS match (nếu có query text)
        if query.strip():
            fts_q = _build_fts_query(query)
            base = """
                SELECT p.*, fts.rank AS fts_rank
                FROM properties_fts fts
                JOIN properties p ON p.id = fts.id
                WHERE properties_fts MATCH ?
            """
            params.append(fts_q)
        else:
            base = "SELECT p.*, 0 AS fts_rank FROM properties p WHERE 1=1"

        # Structured filters
        f = filters or {}
        if f.get("loai"):
            conditions.append("p.loai = ?")
            params.append(f["loai"])
        if f.get("trang_thai"):
            conditions.append("p.trang_thai = ?")
            params.append(f["trang_thai"])
        if f.get("tinh_thanh"):
            conditions.append("p.tinh_thanh LIKE ?")
            params.append(f"%{f['tinh_thanh']}%")
        if f.get("quan_huyen"):
            conditions.append("p.quan_huyen LIKE ?")
            params.append(f"%{f['quan_huyen']}%")
        if f.get("gia_ban_min") is not None:
            conditions.append("p.gia_ban >= ?")
            params.append(f["gia_ban_min"])
        if f.get("gia_ban_max") is not None:
            conditions.append("p.gia_ban <= ?")
            params.append(f["gia_ban_max"])
        if f.get("gia_thue_min") is not None:
            conditions.append("p.gia_thue >= ?")
            params.append(f["gia_thue_min"])
        if f.get("gia_thue_max") is not None:
            conditions.append("p.gia_thue <= ?")
            params.append(f["gia_thue_max"])
        if f.get("dien_tich_min") is not None:
            conditions.append("(p.dien_tich_san >= ? OR p.dien_tich_dat >= ?)")
            params.extend([f["dien_tich_min"], f["dien_tich_min"]])
        if f.get("dien_tich_max") is not None:
            conditions.append("(p.dien_tich_san <= ? OR p.dien_tich_dat <= ?)")
            params.extend([f["dien_tich_max"], f["dien_tich_max"]])
        if f.get("so_phong_ngu_min") is not None:
            conditions.append("p.so_phong_ngu >= ?")
            params.append(f["so_phong_ngu_min"])
        if f.get("phap_ly"):
            conditions.append("p.phap_ly = ?")
            params.append(f["phap_ly"])

        where_extra = (" AND " + " AND ".join(conditions)) if conditions else ""
        sql = f"{base}{where_extra} ORDER BY fts_rank LIMIT ?"
        params.append(top_k)

        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    except Exception as e:
        print(f"[FTSSearch] Error: {e}")
        return []
    finally:
        if close_after:
            conn.close()


def vector_search(query: str, top_k: int = 30) -> list[dict]:
    """Tìm kiếm ngữ nghĩa bằng ChromaDB."""
    col, model = _get_chroma()
    if col is None or col.count() == 0:
        return []
    try:
        embedding = model.encode(query).tolist()
        results = col.query(
            query_embeddings=[embedding],
            n_results=min(top_k, col.count()),
            include=["metadatas", "distances"],
        )
        ids = [int(m["id"]) for m in results["metadatas"][0]]
        distances = results["distances"][0]

        if not ids:
            return []

        conn = get_connection()
        placeholders = ",".join("?" * len(ids))
        rows = conn.execute(
            f"SELECT * FROM properties WHERE id IN ({placeholders})", ids
        ).fetchall()
        conn.close()

        id_to_row = {r["id"]: dict(r) for r in rows}
        # Gắn điểm distance để dùng khi RRF
        ordered = []
        for pid, dist in zip(ids, distances):
            if pid in id_to_row:
                r = id_to_row[pid].copy()
                r["_vector_dist"] = dist
                ordered.append(r)
        return ordered

    except Exception as e:
        print(f"[VectorSearch] Error: {e}")
        return []


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion (RRF) merge
# ---------------------------------------------------------------------------

def hybrid_search(
    query: str,
    filters: Optional[dict] = None,
    top_k: int = 15,
    rrf_k: int = 60,
) -> list[dict]:
    """
    Merge kết quả FTS và Vector bằng RRF.
    Score RRF = 1/(rrf_k + rank_fts) + 1/(rrf_k + rank_vector)
    """
    fts_results = fts_search(query, filters=filters, top_k=top_k * 2)
    vec_results = vector_search(query, top_k=top_k * 2)

    scores: dict[int, float] = {}

    for rank, row in enumerate(fts_results):
        pid = row["id"]
        scores[pid] = scores.get(pid, 0) + 1.0 / (rrf_k + rank + 1)

    for rank, row in enumerate(vec_results):
        pid = row["id"]
        scores[pid] = scores.get(pid, 0) + 1.0 / (rrf_k + rank + 1)

    if not scores:
        return []

    # Lấy data đầy đủ cho top-K ids theo RRF score
    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)[:top_k]

    # Merge data từ hai nguồn
    all_rows: dict[int, dict] = {}
    for r in fts_results + vec_results:
        all_rows[r["id"]] = r

    # Với id không có trong cache, fetch từ DB
    missing = [pid for pid in sorted_ids if pid not in all_rows]
    if missing:
        conn = get_connection()
        placeholders = ",".join("?" * len(missing))
        rows = conn.execute(
            f"SELECT * FROM properties WHERE id IN ({placeholders})", missing
        ).fetchall()
        conn.close()
        for r in rows:
            all_rows[r["id"]] = dict(r)

    result = []
    for pid in sorted_ids:
        if pid in all_rows:
            row = all_rows[pid].copy()
            row["_rrf_score"] = round(scores[pid], 6)
            result.append(row)

    return result


def format_properties_for_prompt(properties: list[dict]) -> str:
    """Chuyển danh sách BĐS thành đoạn văn bản gọn để inject vào prompt."""
    if not properties:
        return "Không tìm thấy bất động sản phù hợp trong danh mục."

    lines = [f"📋 Tìm thấy {len(properties)} bất động sản phù hợp trong danh mục công ty:\n"]
    for i, p in enumerate(properties, 1):
        gia_info = []
        if p.get("gia_ban"):
            gia_info.append(f"Bán: {p['gia_ban']:,.0f} triệu")
        if p.get("gia_thue"):
            gia_info.append(f"Thuê: {p['gia_thue']:,.0f} triệu/th")

        dt_info = []
        if p.get("dien_tich_san"):
            dt_info.append(f"Sàn {p['dien_tich_san']} m²")
        if p.get("dien_tich_dat"):
            dt_info.append(f"Đất {p['dien_tich_dat']} m²")

        line = (
            f"[{i}] **{p.get('ten', 'N/A')}** (ID: {p['ma_bds']})\n"
            f"    • Loại: {p.get('loai','?')} | Trạng thái: {p.get('trang_thai','?')}\n"
            f"    • Địa chỉ: {p.get('dia_chi','?')}, {p.get('quan_huyen') or ''} {p.get('tinh_thanh','')}\n"
        )
        if dt_info:
            line += f"    • Diện tích: {' | '.join(dt_info)}\n"
        if p.get("so_phong_ngu"):
            line += f"    • {p['so_phong_ngu']} PN, {p.get('so_toilet') or '?'} WC"
            if p.get("so_tang"):
                line += f", {p['so_tang']} tầng"
            line += "\n"
        if gia_info:
            line += f"    • Giá: {' | '.join(gia_info)}\n"
        if p.get("phap_ly"):
            line += f"    • Pháp lý: {p['phap_ly']}\n"
        if p.get("mo_ta"):
            line += f"    • Mô tả: {p['mo_ta'][:150]}{'...' if len(p.get('mo_ta','')) > 150 else ''}\n"
        if p.get("nguoi_phu_trach"):
            line += f"    • Liên hệ: {p['nguoi_phu_trach']}"
            if p.get("so_dien_thoai"):
                line += f" – {p['so_dien_thoai']}"
            line += "\n"
        lines.append(line)

    return "\n".join(lines)
