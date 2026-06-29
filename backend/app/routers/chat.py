"""
Router: /chat — RAG chat kết hợp BĐS portfolio + lịch sử tư vấn
"""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from groq import Groq
from dotenv import load_dotenv

from app.services.search import hybrid_search, fts_search, format_properties_for_prompt
from app.services.consultation_search import (
    hybrid_search_consultations, format_consultation_context,
)

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
router = APIRouter(tags=["Chat"])

BASE_SYSTEM_PROMPT = """Bạn là chuyên gia tư vấn bất động sản hàng đầu Việt Nam với hơn 15 năm kinh nghiệm, \
đang làm việc cho công ty bất động sản này.

Kiến thức chuyên môn:
- Thị trường BĐS tại các thành phố lớn: Hà Nội, TP.HCM, Đà Nẵng, Hải Phòng...
- Loại hình: căn hộ, nhà phố, biệt thự, đất nền, shophouse, BĐS thương mại
- Pháp lý: sổ đỏ/hồng, quy hoạch, thủ tục mua bán, sang nhượng
- Tài chính: vay ngân hàng, lãi suất, đòn bẩy, định giá, dòng tiền cho thuê
- Đầu tư: phân tích tiềm năng tăng giá, rủi ro, ROI

Nguyên tắc tư vấn:
- Ưu tiên giới thiệu BĐS từ DANH MỤC CÔNG TY (nếu có trong context)
- Học từ KINH NGHIỆM TƯ VẤN TRƯỚC: áp dụng cách tiếp cận thành công, tránh lỗi đã gặp
- Phân tích cụ thể: ưu/nhược điểm, giá so sánh thị trường, tiềm năng
- Cảnh báo rủi ro trung thực, hỏi thêm nhu cầu để tư vấn chính xác hơn
- Trả lời bằng tiếng Việt, markdown được phép"""


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "llama-3.3-70b-versatile"
    stream: Optional[bool] = True
    use_portfolio: Optional[bool] = True
    use_consultations: Optional[bool] = True   # NEW: bật/tắt consultation RAG
    filters: Optional[dict] = None


def _build_system_prompt(query: str, filters: Optional[dict], use_consultations: bool) -> str:
    sections = [BASE_SYSTEM_PROMPT, "\n---"]

    # 1. BĐS context
    try:
        prop_results = hybrid_search(query, filters=filters, top_k=12)
        if not prop_results:
            prop_results = fts_search(query, top_k=8)
        if prop_results:
            sections.append(format_properties_for_prompt(prop_results))
    except Exception as e:
        print(f"[RAG-Props] {e}")
        sections.append("⚠️ Không thể tải danh mục BĐS lúc này.")

    # 2. Consultation history context
    if use_consultations:
        try:
            chunks, sessions = hybrid_search_consultations(query, top_k=8)
            consult_ctx = format_consultation_context(chunks, sessions)
            if consult_ctx:
                sections.append("\n---")
                sections.append(consult_ctx)
        except Exception as e:
            print(f"[RAG-Consult] {e}")

    sections.append(
        "\n---\nDựa vào dữ liệu trên để tư vấn. "
        "Nếu không có thông tin phù hợp, hãy tư vấn chung về thị trường."
    )
    return "\n".join(sections)


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        user_query = next(
            (m.content for m in reversed(request.messages) if m.role == "user"), ""
        )

        if request.use_portfolio and user_query:
            system_content = _build_system_prompt(
                user_query, request.filters, request.use_consultations
            )
        else:
            system_content = BASE_SYSTEM_PROMPT

        messages = [{"role": "system", "content": system_content}]
        messages += [{"role": m.role, "content": m.content} for m in request.messages]

        if request.stream:
            async def generate():
                stream = client.chat.completions.create(
                    model=request.model,
                    messages=messages,
                    stream=True,
                    temperature=0.7,
                    max_tokens=2048,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        data = json.dumps(
                            {"content": delta.content, "done": False},
                            ensure_ascii=False,
                        )
                        yield f"data: {data}\n\n"
                yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")

        resp = client.chat.completions.create(
            model=request.model, messages=messages,
            stream=False, temperature=0.7, max_tokens=2048,
        )
        return {"content": resp.choices[0].message.content}

    except Exception as e:
        raise


@router.get("/models")
async def get_models():
    return {
        "models": [
            {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B (Nhanh & Thông minh)"},
            {"id": "llama-3.1-8b-instant",    "name": "Llama 3.1 8B (Siêu nhanh)"},
            {"id": "mixtral-8x7b-32768",       "name": "Mixtral 8x7B (Context dài)"},
            {"id": "gemma2-9b-it",             "name": "Gemma 2 9B"},
        ]
    }
