"""
Consultation Service — CRUD + Import + Analytics — Elasticsearch
"""
from datetime import datetime
from typing import Optional

from app.es_client import get_es, IDX_SESSIONS, IDX_CHUNKS, next_id
from app.services.consultation_search import (
    index_session, index_chunk, index_chunks_batch, index_sessions_batch,
    delete_session_from_index, delete_chunks_for_session,
)

_now = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ─── CRUD Sessions ────────────────────────────────────────────────────────────

def create_session(data: dict) -> dict:
    sid = next_id("consultation_sessions")
    row = {
        **data,
        "id": sid,
        "ket_qua": data.get("ket_qua") or "Chưa chốt",
        "co_transcript": 0,
        "created_at": _now(),
        "updated_at": _now(),
    }
    try:
        index_session(row)
    except Exception:
        pass
    get_es().indices.refresh(index=IDX_SESSIONS)
    return row


def get_session(session_id: int) -> Optional[dict]:
    es = get_es()
    try:
        doc = es.get(index=IDX_SESSIONS, id=str(session_id))
        return doc["_source"]
    except Exception:
        return None


def update_session(session_id: int, data: dict) -> Optional[dict]:
    existing = get_session(session_id)
    if not existing:
        return None
    clean = {k: v for k, v in data.items() if v is not None}
    if not clean:
        return existing
    merged = {**existing, **clean, "id": session_id, "updated_at": _now()}
    try:
        index_session(merged)
    except Exception:
        pass
    get_es().indices.refresh(index=IDX_SESSIONS)
    return merged


def delete_session(session_id: int) -> bool:
    if not get_session(session_id):
        return False
    try:
        delete_session_from_index(session_id)
        get_es().indices.refresh(index=IDX_SESSIONS)
        get_es().indices.refresh(index=IDX_CHUNKS)
        return True
    except Exception:
        return False


def list_sessions(
    page: int = 1,
    page_size: int = 20,
    ket_qua: str = None,
    nguoi_tu_van: str = None,
    loai_nhu_cau: str = None,
    khu_vuc: str = None,
    tu_ngay: str = None,
    den_ngay: str = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> dict:
    es = get_es()

    filt = []
    if ket_qua: filt.append({"term": {"ket_qua": ket_qua}})
    if nguoi_tu_van: filt.append({"match": {"nguoi_tu_van": nguoi_tu_van}})
    if loai_nhu_cau: filt.append({"term": {"loai_nhu_cau": loai_nhu_cau}})
    if khu_vuc: filt.append({"match": {"khu_vuc_quan_tam": khu_vuc}})
    if tu_ngay or den_ngay:
        rng = {}
        if tu_ngay: rng["gte"] = tu_ngay
        if den_ngay: rng["lte"] = den_ngay + " 23:59:59"
        filt.append({"range": {"created_at": rng}})

    query = {"bool": {"filter": filt}} if filt else {"match_all": {}}

    safe_sort_map = {
        "created_at": "created_at", "thoi_gian_bat_dau": "thoi_gian_bat_dau",
        "diem_chat_luong": "diem_chat_luong", "thoi_luong_phut": "thoi_luong_phut",
    }
    sort_field = safe_sort_map.get(sort_by, "created_at")
    sort_order = "asc" if sort_dir.lower() == "asc" else "desc"

    offset = (page - 1) * page_size
    resp = es.search(
        index=IDX_SESSIONS,
        query=query,
        sort=[{sort_field: {"order": sort_order}}],
        from_=offset,
        size=page_size,
        track_total_hits=True,
    )

    total = resp["hits"]["total"]["value"]
    items = [hit["_source"] for hit in resp["hits"]["hits"]]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
        "items": items,
    }


# ─── Transcript Chunks ────────────────────────────────────────────────────────

def save_transcript_chunks(session_id: int, chunks: list[dict]) -> int:
    """Lưu danh sách chunks, xóa cũ trước."""
    delete_chunks_for_session(session_id)

    inserted = []
    for idx, c in enumerate(chunks):
        cid = next_id("transcript_chunks")
        topics = c.get("topics", [])
        topics_str = ", ".join(topics) if isinstance(topics, list) else (topics or "")
        row = {
            "id": cid,
            "session_id": session_id,
            "chunk_index": idx,
            "speaker": c.get("speaker", "unknown"),
            "content": c.get("content", ""),
            "start_time": c.get("start_time"),
            "end_time": c.get("end_time"),
            "topics": topics_str,
            "sentiment": c.get("sentiment"),
            "created_at": _now(),
        }
        inserted.append(row)

    try:
        index_chunks_batch(inserted)
    except Exception:
        pass

    update_session(session_id, {"co_transcript": 1})
    get_es().indices.refresh(index=IDX_CHUNKS)
    return len(inserted)


def get_transcript(session_id: int) -> list[dict]:
    es = get_es()
    resp = es.search(
        index=IDX_CHUNKS,
        query={"term": {"session_id": session_id}},
        sort=[{"chunk_index": {"order": "asc"}}],
        size=1000,
    )
    return [hit["_source"] for hit in resp["hits"]["hits"]]


# ─── Import ───────────────────────────────────────────────────────────────────

_SESSION_ALIASES = {
    "session_code": "ma_session", "code": "ma_session",
    "customer": "ten_kh", "customer_name": "ten_kh",
    "phone": "dien_thoai_kh",
    "channel": "kenh_tiep_can",
    "consultant": "nguoi_tu_van", "agent": "nguoi_tu_van",
    "need_type": "loai_nhu_cau", "need": "loai_nhu_cau",
    "property_type": "loai_bds_quan_tam",
    "area": "khu_vuc_quan_tam", "location": "khu_vuc_quan_tam",
    "budget_min": "ngan_sach_min",
    "budget_max": "ngan_sach_max",
    "criteria": "tieu_chi_khac",
    "result": "ket_qua", "outcome": "ket_qua",
    "reject_reason": "ly_do_tu_choi",
    "note": "ghi_chu", "notes": "ghi_chu",
    "start_time": "thoi_gian_bat_dau",
    "end_time": "thoi_gian_ket_thuc",
    "duration": "thoi_luong_phut",
}

_ALLOWED_COLS = {
    "ma_session", "ten_kh", "dien_thoai_kh", "kenh_tiep_can", "nguoi_tu_van",
    "loai_nhu_cau", "loai_bds_quan_tam", "khu_vuc_quan_tam",
    "ngan_sach_min", "ngan_sach_max", "dien_tich_yc", "so_pn_yc", "tieu_chi_khac",
    "ket_qua", "bds_chot_id", "bds_da_gioi_thieu", "ly_do_tu_choi", "ghi_chu",
    "thoi_gian_bat_dau", "thoi_gian_ket_thuc", "thoi_luong_phut",
}


def import_sessions(records: list[dict]) -> dict:
    success, failed, errors = 0, 0, []
    inserted_sessions = []

    for i, rec in enumerate(records):
        try:
            norm = {}
            for k, v in rec.items():
                key = k.strip().lower().replace(" ", "_")
                mapped = _SESSION_ALIASES.get(key, key)
                if mapped in _ALLOWED_COLS and v is not None and str(v).strip() not in ("", "nan", "none", "null"):
                    norm[mapped] = v

            if not norm:
                failed += 1
                errors.append(f"Dòng {i+1}: Không có trường hợp lệ")
                continue

            sid = next_id("consultation_sessions")
            row = {
                **norm, "id": sid,
                "ket_qua": norm.get("ket_qua") or "Chưa chốt",
                "co_transcript": 0,
                "created_at": _now(),
                "updated_at": _now(),
            }
            inserted_sessions.append(row)
            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"Dòng {i+1}: {str(e)[:100]}")

    if inserted_sessions:
        try:
            index_sessions_batch(inserted_sessions)
        except Exception as e:
            print(f"[ConsultIndex] Batch index warning: {e}")

    return {
        "total": len(records),
        "success": success,
        "failed": failed,
        "errors": errors[:20],
    }


# ─── Analytics ────────────────────────────────────────────────────────────────

def get_consultation_stats() -> dict:
    es = get_es()
    total = es.count(index=IDX_SESSIONS)["count"]

    agg_resp = es.search(
        index=IDX_SESSIONS,
        size=0,
        aggs={
            "by_ket_qua": {"terms": {"field": "ket_qua", "size": 10}},
            "by_loai": {"terms": {"field": "loai_nhu_cau", "size": 10}},
            "by_nguoi": {
                "terms": {"field": "nguoi_tu_van.keyword", "size": 10},
                "aggs": {
                    "chot": {
                        "filter": {"term": {"ket_qua": "Chốt giao dịch"}},
                    }
                },
            },
            "by_khu_vuc": {"terms": {"field": "khu_vuc_quan_tam.keyword", "size": 10}},
            "avg_duration": {"avg": {"field": "thoi_luong_phut"}},
            "avg_score": {"avg": {"field": "diem_chat_luong"}},
            "ly_do": {"terms": {"field": "ly_do_tu_choi.keyword", "size": 5}},
        },
    )
    aggs = agg_resp["aggregations"]

    by_ket_qua = [{"ket_qua": b["key"], "cnt": b["doc_count"]} for b in aggs["by_ket_qua"]["buckets"]]
    chot = next((r["cnt"] for r in by_ket_qua if r["ket_qua"] == "Chốt giao dịch"), 0)
    ti_le_chot = round(chot / total * 100, 1) if total > 0 else 0

    return {
        "total": total,
        "ti_le_chot": ti_le_chot,
        "so_chot": chot,
        "avg_duration_phut": round(aggs["avg_duration"]["value"] or 0, 1),
        "avg_diem_chat_luong": round(aggs["avg_score"]["value"] or 0, 1),
        "by_ket_qua": by_ket_qua,
        "by_loai_nhu_cau": [{"loai_nhu_cau": b["key"], "cnt": b["doc_count"]} for b in aggs["by_loai"]["buckets"]],
        "by_nguoi_tu_van": [
            {"nguoi_tu_van": b["key"], "total": b["doc_count"], "chot": b["chot"]["doc_count"]}
            for b in aggs["by_nguoi"]["buckets"]
        ],
        "by_khu_vuc": [{"khu_vuc_quan_tam": b["key"], "cnt": b["doc_count"]} for b in aggs["by_khu_vuc"]["buckets"]],
        "ly_do_tu_choi_pho_bien": [{"ly_do_tu_choi": b["key"], "cnt": b["doc_count"]} for b in aggs["ly_do"]["buckets"]],
    }
