"""
Router: /properties – CRUD + Import + Stats
"""
import csv
import io
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File

from app.models import PropertyCreate, PropertyUpdate, ImportResult
from app.services.property_service import (
    create_property, get_property, update_property,
    delete_property, list_properties, import_from_records, get_stats,
)

router = APIRouter(prefix="/properties", tags=["Properties"])


@router.get("/stats")
async def stats():
    return get_stats()


@router.get("")
async def list_props(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    loai: Optional[str] = None,
    trang_thai: Optional[str] = None,
    tinh_thanh: Optional[str] = None,
    quan_huyen: Optional[str] = None,
    gia_ban_min: Optional[float] = None,
    gia_ban_max: Optional[float] = None,
    gia_thue_min: Optional[float] = None,
    gia_thue_max: Optional[float] = None,
    dien_tich_min: Optional[float] = None,
    dien_tich_max: Optional[float] = None,
    so_phong_ngu_min: Optional[int] = None,
    phap_ly: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|gia_ban|gia_thue|dien_tich_san|ten)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
):
    return list_properties(
        page=page, page_size=page_size,
        loai=loai, trang_thai=trang_thai,
        tinh_thanh=tinh_thanh, quan_huyen=quan_huyen,
        gia_ban_min=gia_ban_min, gia_ban_max=gia_ban_max,
        gia_thue_min=gia_thue_min, gia_thue_max=gia_thue_max,
        dien_tich_min=dien_tich_min, dien_tich_max=dien_tich_max,
        so_phong_ngu_min=so_phong_ngu_min, phap_ly=phap_ly,
        sort_by=sort_by, sort_dir=sort_dir,
    )


@router.post("", status_code=201)
async def create_prop(data: PropertyCreate):
    return create_property(data)


@router.get("/{prop_id}")
async def get_prop(prop_id: int):
    prop = get_property(prop_id)
    if not prop:
        raise HTTPException(404, "Không tìm thấy BĐS")
    return prop


@router.put("/{prop_id}")
async def update_prop(prop_id: int, data: PropertyUpdate):
    prop = update_property(prop_id, data)
    if not prop:
        raise HTTPException(404, "Không tìm thấy BĐS")
    return prop


@router.delete("/{prop_id}")
async def delete_prop(prop_id: int):
    if not delete_property(prop_id):
        raise HTTPException(404, "Không tìm thấy BĐS")
    return {"message": "Đã xóa thành công"}


@router.post("/import/json", response_model=ImportResult)
async def import_json(file: UploadFile = File(...)):
    """Import từ file JSON (array of objects)."""
    if not file.filename.endswith(".json"):
        raise HTTPException(400, "Chỉ hỗ trợ file .json")
    content = await file.read()
    try:
        records = json.loads(content)
        if not isinstance(records, list):
            raise ValueError("File JSON phải là array")
    except Exception as e:
        raise HTTPException(400, f"JSON không hợp lệ: {e}")
    return import_from_records(records)


@router.post("/import/csv", response_model=ImportResult)
async def import_csv(file: UploadFile = File(...)):
    """Import từ file CSV (UTF-8, header row)."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Chỉ hỗ trợ file .csv")
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")  # handle BOM
        reader = csv.DictReader(io.StringIO(text))
        records = list(reader)
    except Exception as e:
        raise HTTPException(400, f"CSV không hợp lệ: {e}")
    return import_from_records(records)


@router.post("/import/reindex")
async def reindex_all():
    """Re-index toàn bộ BĐS vào Elasticsearch (rebuild embeddings)."""
    from app.es_client import get_es, IDX_PROPERTIES
    from app.services.search import index_properties_batch

    es = get_es()
    resp = es.search(index=IDX_PROPERTIES, query={"match_all": {}}, size=10000)
    rows = [hit["_source"] for hit in resp["hits"]["hits"]]
    if not rows:
        return {"message": "Không có dữ liệu để index"}
    index_properties_batch(rows)
    return {"message": f"Đã index {len(rows)} BĐS vào Elasticsearch"}
