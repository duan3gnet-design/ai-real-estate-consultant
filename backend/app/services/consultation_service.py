"""
Consultation Service — CRUD + Import + Analytics + AI Analysis
"""
import csv
import io
import json
from typing import Optional
from app.database import get_connection
from app.services.consultation_search import (
    index_session, index_chunk, index_chunks_batch, index_sessions_batch,
    delete_session_from_index,
)


# ─── CRUD Sessions ────────────────────────────────────────────────────────────

def create_session(data: dict) -> dict:
    conn = get_connection()
    try:
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        cur = conn.execute(
            f"INSERT INTO consultation_sessions ({cols}) VALUES ({placeholders})",
            list(data.values()),
        )
        conn.commit()
        sid = cur.lastrowid
        row = dict(conn.execute(
            "SELECT * FROM consultation_sessions WHERE id = ?", (sid,)
        ).fetchone())
        try:
            index_session(row)
        except Exception:
            pass
        return row
    finally:
        conn.close()


def get_session(session_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM consultation_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_session(session_id: int, data: dict) -> Optional[dict]:
    conn = get_connection()
    try:
        clean = {k: v for k, v in data.items() if v is not None}
        if not clean:
            return get_session(session_id)
        set_clause = ", ".join(f"{k} = ?" for k in clean)
        conn.execute(
            f"UPDATE consultation_sessions SET {set_clause} WHERE id = ?",
            list(clean.values()) + [session_id],
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM consultation_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row:
            r = dict(row)
            try:
                index_session(r)
            except Exception:
                pass
            return r
        return None
    finally:
        conn.close()


def delete_session(session_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM consultation_sessions WHERE id = ?", (session_id,)
        )
        conn.commit()
        if cur.rowcount > 0:
            try:
                delete_session_from_index(session_id)
            except Exception:
                pass
            return True
        return False
    finally:
        conn.close()


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
    conn = get_connection()
    try:
        conds, params = [], []
        if ket_qua:
            conds.append("ket_qua = ?"); params.append(ket_qua)
        if nguoi_tu_van:
            conds.append("nguoi_tu_van LIKE ?"); params.append(f"%{nguoi_tu_van}%")
        if loai_nhu_cau:
            conds.append("loai_nhu_cau = ?"); params.append(loai_nhu_cau)
        if khu_vuc:
            conds.append("khu_vuc_quan_tam LIKE ?"); params.append(f"%{khu_vuc}%")
        if tu_ngay:
            conds.append("created_at >= ?"); params.append(tu_ngay)
        if den_ngay:
            conds.append("created_at <= ?"); params.append(den_ngay + " 23:59:59")

        where = ("WHERE " + " AND ".join(conds)) if conds else ""
        safe_sort = sort_by if sort_by in (
            "created_at", "thoi_gian_bat_dau", "diem_chat_luong", "thoi_luong_phut"
        ) else "created_at"
        safe_dir = "ASC" if sort_dir.lower() == "asc" else "DESC"

        total = conn.execute(
            f"SELECT COUNT(*) FROM consultation_sessions {where}", params
        ).fetchone()[0]
        offset = (page - 1) * page_size
        rows = conn.execute(
            f"SELECT * FROM consultation_sessions {where} "
            f"ORDER BY {safe_sort} {safe_dir} LIMIT ? OFFSET ?",
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


# ─── Transcript Chunks ────────────────────────────────────────────────────────

def save_transcript_chunks(session_id: int, chunks: list[dict]) -> int:
    """Lưu danh sách chunks, xóa cũ trước. Trả về số chunks đã lưu."""
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM transcript_chunks WHERE session_id = ?", (session_id,)
        )
        inserted = []
        for idx, c in enumerate(chunks):
            cur = conn.execute(
                """INSERT INTO transcript_chunks
                   (session_id, chunk_index, speaker, content, start_time, end_time, topics, sentiment)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id, idx,
                    c.get("speaker", "unknown"),
                    c.get("content", ""),
                    c.get("start_time"),
                    c.get("end_time"),
                    json.dumps(c.get("topics", []), ensure_ascii=False) if isinstance(c.get("topics"), list) else c.get("topics", ""),
                    c.get("sentiment"),
                ),
            )
            inserted.append({"id": cur.lastrowid, "session_id": session_id, **c})
        conn.execute(
            "UPDATE consultation_sessions SET co_transcript=1 WHERE id=?", (session_id,)
        )
        conn.commit()
        try:
            index_chunks_batch(inserted)
        except Exception:
            pass
        return len(inserted)
    finally:
        conn.close()


def get_transcript(session_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM transcript_chunks WHERE session_id = ? ORDER BY chunk_index",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


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

    conn = get_connection()
    try:
        for i, rec in enumerate(records):
            try:
                # Normalize keys
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

                cols = ", ".join(norm.keys())
                placeholders = ", ".join("?" * len(norm))
                cur = conn.execute(
                    f"INSERT OR IGNORE INTO consultation_sessions ({cols}) VALUES ({placeholders})",
                    list(norm.values()),
                )
                if cur.lastrowid:
                    inserted_sessions.append({"id": cur.lastrowid, **norm})
                    success += 1
                else:
                    failed += 1
                    errors.append(f"Dòng {i+1}: Trùng mã session hoặc lỗi")
            except Exception as e:
                failed += 1
                errors.append(f"Dòng {i+1}: {str(e)[:100]}")

        conn.commit()
    finally:
        conn.close()

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
    conn = get_connection()
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM consultation_sessions"
        ).fetchone()[0]

        by_ket_qua = conn.execute(
            "SELECT ket_qua, COUNT(*) cnt FROM consultation_sessions GROUP BY ket_qua ORDER BY cnt DESC"
        ).fetchall()

        by_loai = conn.execute(
            "SELECT loai_nhu_cau, COUNT(*) cnt FROM consultation_sessions "
            "WHERE loai_nhu_cau IS NOT NULL GROUP BY loai_nhu_cau ORDER BY cnt DESC"
        ).fetchall()

        by_nguoi = conn.execute(
            "SELECT nguoi_tu_van, COUNT(*) total, "
            "SUM(CASE WHEN ket_qua='Chốt giao dịch' THEN 1 ELSE 0 END) chot "
            "FROM consultation_sessions WHERE nguoi_tu_van IS NOT NULL "
            "GROUP BY nguoi_tu_van ORDER BY total DESC LIMIT 10"
        ).fetchall()

        by_khu_vuc = conn.execute(
            "SELECT khu_vuc_quan_tam, COUNT(*) cnt FROM consultation_sessions "
            "WHERE khu_vuc_quan_tam IS NOT NULL GROUP BY khu_vuc_quan_tam ORDER BY cnt DESC LIMIT 10"
        ).fetchall()

        avg_duration = conn.execute(
            "SELECT AVG(thoi_luong_phut) FROM consultation_sessions WHERE thoi_luong_phut > 0"
        ).fetchone()[0]

        avg_score = conn.execute(
            "SELECT AVG(diem_chat_luong) FROM consultation_sessions WHERE diem_chat_luong IS NOT NULL"
        ).fetchone()[0]

        # Tỷ lệ chốt
        chot = next((r["cnt"] for r in by_ket_qua if r["ket_qua"] == "Chốt giao dịch"), 0)
        ti_le_chot = round(chot / total * 100, 1) if total > 0 else 0

        # Lý do từ chối phổ biến
        ly_do = conn.execute(
            "SELECT ly_do_tu_choi, COUNT(*) cnt FROM consultation_sessions "
            "WHERE ly_do_tu_choi IS NOT NULL AND ly_do_tu_choi != '' "
            "GROUP BY ly_do_tu_choi ORDER BY cnt DESC LIMIT 5"
        ).fetchall()

        return {
            "total": total,
            "ti_le_chot": ti_le_chot,
            "so_chot": chot,
            "avg_duration_phut": round(avg_duration or 0, 1),
            "avg_diem_chat_luong": round(avg_score or 0, 1),
            "by_ket_qua": [dict(r) for r in by_ket_qua],
            "by_loai_nhu_cau": [dict(r) for r in by_loai],
            "by_nguoi_tu_van": [dict(r) for r in by_nguoi],
            "by_khu_vuc": [dict(r) for r in by_khu_vuc],
            "ly_do_tu_choi_pho_bien": [dict(r) for r in ly_do],
        }
    finally:
        conn.close()
