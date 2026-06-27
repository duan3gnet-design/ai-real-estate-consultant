"""
Property CRUD Service
"""
import sqlite3
from typing import Optional
from app.database import get_connection
from app.models import PropertyCreate, PropertyUpdate
from app.services.search import index_property, index_properties_batch, delete_from_index


def create_property(data: PropertyCreate) -> dict:
    conn = get_connection()
    try:
        d = data.model_dump()
        cols = ", ".join(d.keys())
        placeholders = ", ".join("?" * len(d))
        values = list(d.values())
        cur = conn.execute(
            f"INSERT INTO properties ({cols}) VALUES ({placeholders})", values
        )
        conn.commit()
        prop_id = cur.lastrowid
        row = conn.execute("SELECT * FROM properties WHERE id = ?", (prop_id,)).fetchone()
        row_dict = dict(row)
        # Index vào vector store (async không cần thiết, nhẹ)
        try:
            index_property(prop_id, row_dict)
        except Exception as e:
            print(f"[VectorIndex] Warning: {e}")
        return row_dict
    finally:
        conn.close()


def get_property(prop_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM properties WHERE id = ?", (prop_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_property(prop_id: int, data: PropertyUpdate) -> Optional[dict]:
    conn = get_connection()
    try:
        d = {k: v for k, v in data.model_dump().items() if v is not None}
        if not d:
            return get_property(prop_id)
        set_clause = ", ".join(f"{k} = ?" for k in d)
        values = list(d.values()) + [prop_id]
        conn.execute(f"UPDATE properties SET {set_clause} WHERE id = ?", values)
        conn.commit()
        row = conn.execute("SELECT * FROM properties WHERE id = ?", (prop_id,)).fetchone()
        if row:
            row_dict = dict(row)
            try:
                index_property(prop_id, row_dict)
            except Exception:
                pass
            return row_dict
        return None
    finally:
        conn.close()


def delete_property(prop_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM properties WHERE id = ?", (prop_id,))
        conn.commit()
        if cur.rowcount > 0:
            try:
                delete_from_index(prop_id)
            except Exception:
                pass
            return True
        return False
    finally:
        conn.close()


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
    conn = get_connection()
    try:
        conditions = []
        params = []

        if loai:
            conditions.append("loai = ?"); params.append(loai)
        if trang_thai:
            conditions.append("trang_thai = ?"); params.append(trang_thai)
        if tinh_thanh:
            conditions.append("tinh_thanh LIKE ?"); params.append(f"%{tinh_thanh}%")
        if quan_huyen:
            conditions.append("quan_huyen LIKE ?"); params.append(f"%{quan_huyen}%")
        if gia_ban_min is not None:
            conditions.append("gia_ban >= ?"); params.append(gia_ban_min)
        if gia_ban_max is not None:
            conditions.append("gia_ban <= ?"); params.append(gia_ban_max)
        if gia_thue_min is not None:
            conditions.append("gia_thue >= ?"); params.append(gia_thue_min)
        if gia_thue_max is not None:
            conditions.append("gia_thue <= ?"); params.append(gia_thue_max)
        if dien_tich_min is not None:
            conditions.append("(dien_tich_san >= ? OR dien_tich_dat >= ?)")
            params.extend([dien_tich_min, dien_tich_min])
        if dien_tich_max is not None:
            conditions.append("(dien_tich_san <= ? OR dien_tich_dat <= ?)")
            params.extend([dien_tich_max, dien_tich_max])
        if so_phong_ngu_min is not None:
            conditions.append("so_phong_ngu >= ?"); params.append(so_phong_ngu_min)
        if phap_ly:
            conditions.append("phap_ly = ?"); params.append(phap_ly)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        safe_sort = sort_by if sort_by in ("created_at", "gia_ban", "gia_thue", "dien_tich_san", "ten") else "created_at"
        safe_dir = "ASC" if sort_dir.lower() == "asc" else "DESC"

        total = conn.execute(f"SELECT COUNT(*) FROM properties {where}", params).fetchone()[0]
        offset = (page - 1) * page_size
        rows = conn.execute(
            f"SELECT * FROM properties {where} ORDER BY {safe_sort} {safe_dir} LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "items": [dict(r) for r in rows],
        }
    finally:
        conn.close()


def import_from_records(records: list[dict]) -> dict:
    """Bulk import từ list dicts (CSV/JSON). Trả về kết quả."""
    from app.models import PropertyCreate
    success, failed, errors = 0, 0, []
    inserted_rows = []

    conn = get_connection()
    try:
        for i, rec in enumerate(records):
            try:
                # Map flexible column names
                normalized = _normalize_record(rec)
                data = PropertyCreate(**normalized)
                d = data.model_dump()
                cols = ", ".join(d.keys())
                placeholders = ", ".join("?" * len(d))
                cur = conn.execute(
                    f"INSERT OR IGNORE INTO properties ({cols}) VALUES ({placeholders})",
                    list(d.values()),
                )
                if cur.lastrowid:
                    inserted_rows.append({"id": cur.lastrowid, **d})
                    success += 1
                else:
                    failed += 1
                    errors.append(f"Dòng {i+1}: Trùng mã BĐS hoặc lỗi")
            except Exception as e:
                failed += 1
                errors.append(f"Dòng {i+1}: {str(e)[:100]}")

        conn.commit()
    finally:
        conn.close()

    # Bulk index vector
    if inserted_rows:
        try:
            index_properties_batch(inserted_rows)
        except Exception as e:
            print(f"[VectorIndex] Batch index warning: {e}")

    return {"total": len(records), "success": success, "failed": failed, "errors": errors[:20]}


def get_stats() -> dict:
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
        by_loai = conn.execute(
            "SELECT loai, COUNT(*) as cnt FROM properties GROUP BY loai ORDER BY cnt DESC"
        ).fetchall()
        by_tinh = conn.execute(
            "SELECT tinh_thanh, COUNT(*) as cnt FROM properties GROUP BY tinh_thanh ORDER BY cnt DESC LIMIT 10"
        ).fetchall()
        by_trang_thai = conn.execute(
            "SELECT trang_thai, COUNT(*) as cnt FROM properties GROUP BY trang_thai"
        ).fetchall()
        avg_gia = conn.execute(
            "SELECT AVG(gia_ban) as avg_ban, AVG(gia_thue) as avg_thue FROM properties WHERE gia_ban > 0 OR gia_thue > 0"
        ).fetchone()
        return {
            "total": total,
            "by_loai": [dict(r) for r in by_loai],
            "by_tinh_thanh": [dict(r) for r in by_tinh],
            "by_trang_thai": [dict(r) for r in by_trang_thai],
            "avg_gia_ban": round(avg_gia["avg_ban"] or 0, 1),
            "avg_gia_thue": round(avg_gia["avg_thue"] or 0, 1),
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FIELD_ALIASES = {
    # Tiếng Anh
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
    """Map các tên cột khác nhau về tên chuẩn."""
    out = {}
    for k, v in rec.items():
        key = k.strip().lower().replace(" ", "_")
        mapped = _FIELD_ALIASES.get(key, key)
        if v is not None and str(v).strip() not in ("", "nan", "none", "null", "N/A"):
            out[mapped] = v
    return out
