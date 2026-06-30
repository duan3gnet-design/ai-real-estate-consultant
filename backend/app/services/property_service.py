"""
Property CRUD Service — Elasticsearch
"""
from datetime import datetime
from typing import Optional

from app.es_client import get_es, IDX_PROPERTIES, next_id
from app.models import PropertyCreate, PropertyUpdate
from app.services.search import index_property, index_properties_batch, delete_from_index

_now = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_property(data: PropertyCreate) -> dict:
    es = get_es()
    d = data.model_dump()
    prop_id = next_id("properties")
    d["id"] = prop_id
    d["created_at"] = _now()
    d["updated_at"] = d["created_at"]

    try:
        index_property(prop_id, d)
    except Exception as e:
        print(f"[VectorIndex] Warning: {e}")

    es.indices.refresh(index=IDX_PROPERTIES)
    return d


def get_property(prop_id: int) -> Optional[dict]:
    es = get_es()
    try:
        doc = es.get(index=IDX_PROPERTIES, id=str(prop_id))
        return doc["_source"]
    except Exception:
        return None


def update_property(prop_id: int, data: PropertyUpdate) -> Optional[dict]:
    existing = get_property(prop_id)
    if not existing:
        return None

    es = get_es()
    d = {k: v for k, v in data.model_dump().items() if v is not None}
    if d:
        merged = {**existing, **d, "id": prop_id, "updated_at": _now()}
        try:
            index_property(prop_id, merged)
        except Exception:
            pass
        es.indices.refresh(index=IDX_PROPERTIES)
        return merged
    return existing


def delete_property(prop_id: int) -> bool:
    if not get_property(prop_id):
        return False
    try:
        delete_from_index(prop_id)
        get_es().indices.refresh(index=IDX_PROPERTIES)
        return True
    except Exception:
        return False


def list_properties(
    page: int = 1,
    page_size: int = 20,
    loai: str = None,
    trang_thai: str = None,
    tinh_thanh: str = None,
    quan_huyen: str = None,
    gia_ban_min: float = None,
    gia_ban_max: float = None,
    gia_thue_min: float = None,
    gia_thue_max: float = None,
    dien_tich_min: float = None,
    dien_tich_max: float = None,
    so_phong_ngu_min: int = None,
    phap_ly: str = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> dict:
    es = get_es()

    filt = []
    if loai: filt.append({"term": {"loai": loai}})
    if trang_thai: filt.append({"term": {"trang_thai": trang_thai}})
    if tinh_thanh: filt.append({"match": {"tinh_thanh": tinh_thanh}})
    if quan_huyen: filt.append({"match": {"quan_huyen": quan_huyen}})
    if gia_ban_min is not None or gia_ban_max is not None:
        rng = {}
        if gia_ban_min is not None: rng["gte"] = gia_ban_min
        if gia_ban_max is not None: rng["lte"] = gia_ban_max
        filt.append({"range": {"gia_ban": rng}})
    if gia_thue_min is not None or gia_thue_max is not None:
        rng = {}
        if gia_thue_min is not None: rng["gte"] = gia_thue_min
        if gia_thue_max is not None: rng["lte"] = gia_thue_max
        filt.append({"range": {"gia_thue": rng}})
    if dien_tich_min is not None or dien_tich_max is not None:
        rng = {}
        if dien_tich_min is not None: rng["gte"] = dien_tich_min
        if dien_tich_max is not None: rng["lte"] = dien_tich_max
        filt.append({"bool": {"should": [
            {"range": {"dien_tich_san": rng}}, {"range": {"dien_tich_dat": rng}},
        ], "minimum_should_match": 1}})
    if so_phong_ngu_min is not None:
        filt.append({"range": {"so_phong_ngu": {"gte": so_phong_ngu_min}}})
    if phap_ly: filt.append({"term": {"phap_ly": phap_ly}})

    query = {"bool": {"filter": filt}} if filt else {"match_all": {}}

    safe_sort_map = {
        "created_at": "created_at", "gia_ban": "gia_ban", "gia_thue": "gia_thue",
        "dien_tich_san": "dien_tich_san", "ten": "ten.keyword",
    }
    sort_field = safe_sort_map.get(sort_by, "created_at")
    sort_order = "asc" if sort_dir.lower() == "asc" else "desc"

    offset = (page - 1) * page_size
    resp = es.search(
        index=IDX_PROPERTIES,
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


def import_from_records(records: list[dict]) -> dict:
    """Bulk import từ list dicts (CSV/JSON)."""
    success, failed, errors = 0, 0, []
    inserted_rows = []

    for i, rec in enumerate(records):
        try:
            normalized = _normalize_record(rec)
            data = PropertyCreate(**normalized)
            d = data.model_dump()
            prop_id = next_id("properties")
            d["id"] = prop_id
            d["created_at"] = _now()
            d["updated_at"] = d["created_at"]
            inserted_rows.append(d)
            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"Dòng {i+1}: {str(e)[:100]}")

    if inserted_rows:
        try:
            index_properties_batch(inserted_rows)
        except Exception as e:
            print(f"[VectorIndex] Batch index warning: {e}")

    return {"total": len(records), "success": success, "failed": failed, "errors": errors[:20]}


def get_stats() -> dict:
    es = get_es()
    total_resp = es.count(index=IDX_PROPERTIES)
    total = total_resp["count"]

    agg_resp = es.search(
        index=IDX_PROPERTIES,
        size=0,
        aggs={
            "by_loai": {"terms": {"field": "loai", "size": 20}},
            "by_tinh_thanh": {"terms": {"field": "tinh_thanh.keyword", "size": 10}},
            "by_trang_thai": {"terms": {"field": "trang_thai", "size": 10}},
            "avg_gia_ban": {"avg": {"field": "gia_ban"}},
            "avg_gia_thue": {"avg": {"field": "gia_thue"}},
        },
    )
    aggs = agg_resp["aggregations"]

    return {
        "total": total,
        "by_loai": [{"loai": b["key"], "cnt": b["doc_count"]} for b in aggs["by_loai"]["buckets"]],
        "by_tinh_thanh": [{"tinh_thanh": b["key"], "cnt": b["doc_count"]} for b in aggs["by_tinh_thanh"]["buckets"]],
        "by_trang_thai": [{"trang_thai": b["key"], "cnt": b["doc_count"]} for b in aggs["by_trang_thai"]["buckets"]],
        "avg_gia_ban": round(aggs["avg_gia_ban"]["value"] or 0, 1),
        "avg_gia_thue": round(aggs["avg_gia_thue"]["value"] or 0, 1),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FIELD_ALIASES = {
    "name": "ten", "title": "ten",
    "type": "loai", "property_type": "loai",
    "status": "trang_thai",
    "address": "dia_chi",
    "ward": "phuong_xa", "district": "quan_huyen", "city": "tinh_thanh", "province": "tinh_thanh",
    "lat": "vi_do", "lng": "kinh_do", "latitude": "vi_do", "longitude": "kinh_do",
    "land_area": "dien_tich_dat", "floor_area": "dien_tich_san", "area": "dien_tich_san",
    "floors": "so_tang", "bedrooms": "so_phong_ngu", "bathrooms": "so_toilet",
    "direction": "huong", "frontage": "mat_tien", "road_width": "duong_vao",
    "sale_price": "gia_ban", "price": "gia_ban",
    "rent_price": "gia_thue", "rent": "gia_thue",
    "purchase_price": "gia_mua_vao",
    "year_purchased": "nam_mua", "purchase_year": "nam_mua",
    "management_fee": "phi_quan_ly",
    "legal": "phap_ly", "legal_status": "phap_ly",
    "year_built": "nam_xay_dung",
    "zoning": "quy_hoach",
    "amenities": "tien_ich", "facilities": "tien_ich",
    "description": "mo_ta", "note": "ghi_chu_noi_bo",
    "contact": "nguoi_phu_trach", "agent": "nguoi_phu_trach",
    "phone": "so_dien_thoai",
    "images": "anh_urls", "photos": "anh_urls",
    "code": "ma_bds", "property_code": "ma_bds",
}


def _normalize_record(rec: dict) -> dict:
    out = {}
    for k, v in rec.items():
        key = k.strip().lower().replace(" ", "_")
        mapped = _FIELD_ALIASES.get(key, key)
        if v is not None and str(v).strip() not in ("", "nan", "none", "null", "N/A"):
            out[mapped] = v
    return out
