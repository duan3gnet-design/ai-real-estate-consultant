"""
Hybrid Search Service — Elasticsearch
=======================================
Kết hợp:
1. Vector Search  – ES kNN trên field `embedding` (dense_vector)
2. Full-text + Filter – ES multi_match + bool filter trên text fields

Merge bằng Reciprocal Rank Fusion (RRF) thủ công (tương thích mọi version ES).
"""
from typing import Optional

from app.es_client import get_es, IDX_PROPERTIES
from app.embedding import embed_text, embed_texts

_TEXT_FIELDS = ["ten^3", "dia_chi^2", "phuong_xa", "quan_huyen^2", "tinh_thanh^2", "loai", "tien_ich", "mo_ta", "quy_hoach"]


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
    return " | ".join(p for p in parts if p and p.strip())


def index_property(prop_id: int, row: dict):
    """Thêm/cập nhật 1 BĐS vào Elasticsearch (kèm embedding)."""
    es = get_es()
    text = _row_to_text(row)
    doc = {k: v for k, v in row.items() if v is not None}
    doc["embedding"] = embed_text(text)
    es.index(index=IDX_PROPERTIES, id=str(prop_id), document=doc)


def index_properties_batch(rows: list[dict], batch_size: int = 500):
    """Bulk index nhiều BĐS bằng ES bulk API."""
    from elasticsearch.helpers import bulk
    es = get_es()

    for i in range(0, len(rows), batch_size):
        batch = rows[i: i + batch_size]
        texts = [_row_to_text(r) for r in batch]
        embeddings = embed_texts(texts, batch_size=64)

        actions = []
        for row, emb in zip(batch, embeddings):
            doc = {k: v for k, v in row.items() if v is not None}
            doc["embedding"] = emb
            actions.append({
                "_index": IDX_PROPERTIES,
                "_id": str(row["id"]),
                "_source": doc,
            })
        bulk(es, actions)

    es.indices.refresh(index=IDX_PROPERTIES)
    print(f"[VectorSearch] Indexed {len(rows)} properties.")


def delete_from_index(prop_id: int):
    es = get_es()
    try:
        es.delete(index=IDX_PROPERTIES, id=str(prop_id))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Full-text search + structured filter
# ---------------------------------------------------------------------------

def _build_filters(filters: Optional[dict]) -> list[dict]:
    f = filters or {}
    must_filters = []

    if f.get("loai"):
        must_filters.append({"term": {"loai": f["loai"]}})
    if f.get("trang_thai"):
        must_filters.append({"term": {"trang_thai": f["trang_thai"]}})
    if f.get("tinh_thanh"):
        must_filters.append({"match": {"tinh_thanh": f["tinh_thanh"]}})
    if f.get("quan_huyen"):
        must_filters.append({"match": {"quan_huyen": f["quan_huyen"]}})
    if f.get("gia_ban_min") is not None or f.get("gia_ban_max") is not None:
        rng = {}
        if f.get("gia_ban_min") is not None: rng["gte"] = f["gia_ban_min"]
        if f.get("gia_ban_max") is not None: rng["lte"] = f["gia_ban_max"]
        must_filters.append({"range": {"gia_ban": rng}})
    if f.get("gia_thue_min") is not None or f.get("gia_thue_max") is not None:
        rng = {}
        if f.get("gia_thue_min") is not None: rng["gte"] = f["gia_thue_min"]
        if f.get("gia_thue_max") is not None: rng["lte"] = f["gia_thue_max"]
        must_filters.append({"range": {"gia_thue": rng}})
    if f.get("dien_tich_min") is not None or f.get("dien_tich_max") is not None:
        rng = {}
        if f.get("dien_tich_min") is not None: rng["gte"] = f["dien_tich_min"]
        if f.get("dien_tich_max") is not None: rng["lte"] = f["dien_tich_max"]
        # OR giữa dien_tich_san và dien_tich_dat
        must_filters.append({
            "bool": {
                "should": [
                    {"range": {"dien_tich_san": rng}},
                    {"range": {"dien_tich_dat": rng}},
                ],
                "minimum_should_match": 1,
            }
        })
    if f.get("so_phong_ngu_min") is not None:
        must_filters.append({"range": {"so_phong_ngu": {"gte": f["so_phong_ngu_min"]}}})
    if f.get("phap_ly"):
        must_filters.append({"term": {"phap_ly": f["phap_ly"]}})

    return must_filters


def fts_search(query: str, filters: Optional[dict] = None, top_k: int = 30) -> list[dict]:
    """Full-text search + structured filter trên Elasticsearch."""
    es = get_es()
    must_filters = _build_filters(filters)

    body = {
        "size": top_k,
        "query": {
            "bool": {
                "filter": must_filters,
            }
        },
    }

    if query.strip():
        body["query"]["bool"]["must"] = [{
            "multi_match": {
                "query": query,
                "fields": _TEXT_FIELDS,
                "fuzziness": "AUTO",
            }
        }]
    else:
        body["query"]["bool"]["must"] = [{"match_all": {}}]

    try:
        resp = es.search(index=IDX_PROPERTIES, body=body)
        return [hit["_source"] for hit in resp["hits"]["hits"]]
    except Exception as e:
        print(f"[FTSSearch] Error: {e}")
        return []


def vector_search(query: str, top_k: int = 30, filters: Optional[dict] = None) -> list[dict]:
    """Vector kNN search trên Elasticsearch."""
    es = get_es()
    embedding = embed_text(query)
    must_filters = _build_filters(filters)

    knn = {
        "field": "embedding",
        "query_vector": embedding,
        "k": top_k,
        "num_candidates": max(top_k * 4, 100),
    }
    if must_filters:
        knn["filter"] = {"bool": {"filter": must_filters}}

    try:
        resp = es.search(index=IDX_PROPERTIES, knn=knn, size=top_k)
        return [hit["_source"] for hit in resp["hits"]["hits"]]
    except Exception as e:
        print(f"[VectorSearch] Error: {e}")
        return []


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion (RRF) merge — thủ công để tương thích mọi version ES
# ---------------------------------------------------------------------------

def hybrid_search(
    query: str,
    filters: Optional[dict] = None,
    top_k: int = 15,
    rrf_k: int = 60,
) -> list[dict]:
    """Merge kết quả FTS và Vector bằng RRF."""
    fts_results = fts_search(query, filters=filters, top_k=top_k * 2)
    vec_results = vector_search(query, top_k=top_k * 2, filters=filters)

    scores: dict[int, float] = {}
    all_rows: dict[int, dict] = {}

    for rank, row in enumerate(fts_results):
        pid = row["id"]
        scores[pid] = scores.get(pid, 0) + 1.0 / (rrf_k + rank + 1)
        all_rows[pid] = row

    for rank, row in enumerate(vec_results):
        pid = row["id"]
        scores[pid] = scores.get(pid, 0) + 1.0 / (rrf_k + rank + 1)
        all_rows.setdefault(pid, row)

    if not scores:
        return []

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)[:top_k]

    result = []
    for pid in sorted_ids:
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
            f"[{i}] **{p.get('ten', 'N/A')}** (ID: {p.get('ma_bds', p.get('id'))})\n"
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
