"""
Router: /consultations — CRUD + Import + Transcript + Analytics + AI Analysis
"""
import csv
import io
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
import os
from groq import Groq
from dotenv import load_dotenv

from app.services.consultation_service import (
    create_session, get_session, update_session, delete_session,
    list_sessions, save_transcript_chunks, get_transcript,
    import_sessions, get_consultation_stats,
)

load_dotenv()
router = APIRouter(prefix="/consultations", tags=["Consultations"])
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ─── Pydantic models ──────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    ma_session: Optional[str] = None
    ten_kh: Optional[str] = None
    dien_thoai_kh: Optional[str] = None
    kenh_tiep_can: Optional[str] = None
    nguoi_tu_van: Optional[str] = None
    loai_nhu_cau: Optional[str] = None
    loai_bds_quan_tam: Optional[str] = None
    khu_vuc_quan_tam: Optional[str] = None
    ngan_sach_min: Optional[float] = None
    ngan_sach_max: Optional[float] = None
    dien_tich_yc: Optional[str] = None
    so_pn_yc: Optional[int] = None
    tieu_chi_khac: Optional[str] = None
    ket_qua: Optional[str] = "Chưa chốt"
    bds_chot_id: Optional[int] = None
    bds_da_gioi_thieu: Optional[str] = None
    ly_do_tu_choi: Optional[str] = None
    ghi_chu: Optional[str] = None
    thoi_gian_bat_dau: Optional[str] = None
    thoi_gian_ket_thuc: Optional[str] = None
    thoi_luong_phut: Optional[int] = None


class ChunkItem(BaseModel):
    speaker: Optional[str] = "unknown"
    content: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    topics: Optional[list] = []
    sentiment: Optional[str] = None


class TranscriptSave(BaseModel):
    chunks: list[ChunkItem]


class AnalyzeRequest(BaseModel):
    session_id: int
    model: Optional[str] = "llama-3.3-70b-versatile"


# ─── CRUD ────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def stats():
    return get_consultation_stats()


@router.get("")
async def list_s(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    ket_qua: Optional[str] = None,
    nguoi_tu_van: Optional[str] = None,
    loai_nhu_cau: Optional[str] = None,
    khu_vuc: Optional[str] = None,
    tu_ngay: Optional[str] = None,
    den_ngay: Optional[str] = None,
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
):
    return list_sessions(
        page=page, page_size=page_size,
        ket_qua=ket_qua, nguoi_tu_van=nguoi_tu_van,
        loai_nhu_cau=loai_nhu_cau, khu_vuc=khu_vuc,
        tu_ngay=tu_ngay, den_ngay=den_ngay,
        sort_by=sort_by, sort_dir=sort_dir,
    )


@router.post("", status_code=201)
async def create_s(data: SessionCreate):
    d = {k: v for k, v in data.model_dump().items() if v is not None}
    return create_session(d)


@router.get("/{sid}")
async def get_s(sid: int):
    s = get_session(sid)
    if not s:
        raise HTTPException(404, "Không tìm thấy session")
    return s


@router.put("/{sid}")
async def update_s(sid: int, data: SessionCreate):
    s = update_session(sid, data.model_dump(exclude_none=True))
    if not s:
        raise HTTPException(404, "Không tìm thấy session")
    return s


@router.delete("/{sid}")
async def delete_s(sid: int):
    if not delete_session(sid):
        raise HTTPException(404, "Không tìm thấy session")
    return {"message": "Đã xóa"}


# ─── Transcript ───────────────────────────────────────────────────────────────

@router.post("/{sid}/transcript")
async def save_transcript(sid: int, data: TranscriptSave):
    if not get_session(sid):
        raise HTTPException(404, "Không tìm thấy session")
    n = save_transcript_chunks(sid, [c.model_dump() for c in data.chunks])
    return {"saved": n}


@router.get("/{sid}/transcript")
async def get_transcript_api(sid: int):
    return get_transcript(sid)


@router.post("/{sid}/transcript/text")
async def upload_raw_transcript(sid: int, file: UploadFile = File(...)):
    """Upload raw text transcript — tự động chunk theo dòng/speaker."""
    if not get_session(sid):
        raise HTTPException(404, "Không tìm thấy session")
    content = (await file.read()).decode("utf-8-sig", errors="ignore")
    chunks = _parse_raw_transcript(content)
    n = save_transcript_chunks(sid, chunks)
    return {"saved": n, "chunks": chunks[:5]}  # preview 5 chunks đầu


# ─── AI Analysis ─────────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze_session(req: AnalyzeRequest):
    """AI phân tích chất lượng một buổi tư vấn, trả về điểm + nhận xét."""
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(404, "Không tìm thấy session")

    chunks = get_transcript(req.session_id)
    transcript_text = "\n".join(
        f"[{c.get('speaker','?')}]: {c.get('content','')}"
        for c in chunks[:60]   # max 60 chunks để tránh tràn context
    )

    session_meta = f"""
Thông tin buổi tư vấn:
- Khách hàng: {session.get('ten_kh') or 'Ẩn danh'}
- Nhu cầu: {session.get('loai_nhu_cau')} | {session.get('loai_bds_quan_tam')} | {session.get('khu_vuc_quan_tam')}
- Ngân sách: {session.get('ngan_sach_min')}–{session.get('ngan_sach_max')} triệu
- Tư vấn viên: {session.get('nguoi_tu_van') or 'N/A'}
- Kết quả: {session.get('ket_qua')}
- Lý do từ chối (nếu có): {session.get('ly_do_tu_choi') or 'N/A'}
"""

    prompt = f"""Bạn là chuyên gia đào tạo tư vấn bất động sản. Hãy phân tích buổi tư vấn dưới đây và trả về JSON theo đúng format sau (KHÔNG trả về gì khác ngoài JSON):

{{
  "diem_tong": <số thực 0-10>,
  "diem_chi_tiet": {{
    "kham_pha_nhu_cau": <0-10>,
    "trinh_bay_san_pham": <0-10>,
    "xu_ly_objection": <0-10>,
    "ky_nang_chot_sale": <0-10>,
    "thai_do_chuyen_nghiep": <0-10>
  }},
  "diem_manh": ["...", "...", "..."],
  "diem_yeu": ["...", "...", "..."],
  "goi_y_cai_thien": ["...", "...", "..."],
  "phan_tich_tom_tat": "2-3 câu tóm tắt ngắn gọn",
  "co_hoi_con_lai": "Cơ hội để tiếp tục với khách hàng này (nếu chưa chốt)"
}}

{session_meta}

TRANSCRIPT:
{transcript_text if transcript_text else '(Không có transcript)'}
"""

    try:
        response = groq_client.chat.completions.create(
            model=req.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content.strip()
        # Làm sạch JSON
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)

        # Lưu điểm và feedback vào DB
        update_session(req.session_id, {
            "diem_chat_luong": result.get("diem_tong"),
            "ai_feedback": json.dumps(result, ensure_ascii=False),
        })
        return result
    except json.JSONDecodeError:
        return {"error": "AI trả về định dạng không hợp lệ", "raw": raw[:500]}
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Import ───────────────────────────────────────────────────────────────────

@router.post("/import/csv")
async def import_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Chỉ hỗ trợ .csv")
    content = await file.read()
    text = content.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    return import_sessions(list(reader))


@router.post("/import/json")
async def import_json_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(400, "Chỉ hỗ trợ .json")
    content = await file.read()
    records = json.loads(content)
    if not isinstance(records, list):
        raise HTTPException(400, "JSON phải là array")
    return import_sessions(records)


@router.post("/reindex")
async def reindex():
    """Re-index toàn bộ sessions + chunks vào vector store."""
    from app.services.consultation_search import index_sessions_batch, index_chunks_batch
    conn = __import__("app.database", fromlist=["get_connection"]).get_connection()
    sessions = [dict(r) for r in conn.execute("SELECT * FROM consultation_sessions").fetchall()]
    chunks = [dict(r) for r in conn.execute("SELECT * FROM transcript_chunks").fetchall()]
    conn.close()
    index_sessions_batch(sessions)
    index_chunks_batch(chunks)
    return {"sessions": len(sessions), "chunks": len(chunks)}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _parse_raw_transcript(text: str) -> list[dict]:
    """Parse transcript dạng text thô thành danh sách chunks.
    Hỗ trợ các format:
    - [TV]: nội dung
    - [KH]: nội dung
    - Tư vấn viên: nội dung
    - Khách hàng: nội dung
    - HH:MM:SS nội dung
    """
    import re
    chunks = []
    lines = text.strip().splitlines()

    speaker_map = {
        "tv": "consultant", "tư vấn": "consultant", "tư vấn viên": "consultant",
        "nvtv": "consultant", "consultant": "consultant", "agent": "consultant",
        "kh": "customer", "khách hàng": "customer", "khach hang": "customer",
        "customer": "customer", "client": "customer",
    }

    current_speaker = "unknown"
    current_lines = []

    def flush():
        content = " ".join(current_lines).strip()
        if content:
            chunks.append({"speaker": current_speaker, "content": content})

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Pattern: [SPEAKER]: content hoặc SPEAKER: content
        m = re.match(r"^\[?([^\]:\n]{1,30})\]?\s*:\s*(.+)$", line, re.IGNORECASE)
        if m:
            flush()
            current_lines = []
            speaker_raw = m.group(1).strip().lower()
            current_speaker = speaker_map.get(speaker_raw, "unknown")
            content = m.group(2).strip()
            if content:
                current_lines.append(content)
        else:
            # Tiếp tục dòng trước
            current_lines.append(line)

    flush()

    # Nếu không parse được → chunk theo đoạn văn
    if not chunks:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for i, p in enumerate(paragraphs):
            chunks.append({
                "speaker": "consultant" if i % 2 == 0 else "customer",
                "content": p[:500],
            })

    return chunks
