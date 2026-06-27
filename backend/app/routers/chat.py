"""
Router: /chat – RAG-powered chat với Hybrid Search
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
- Phân tích cụ thể: ưu/nhược điểm, giá so sánh thị trường, tiềm năng
- Cảnh báo rủi ro trung thực
- Hỏi thêm nhu cầu để tư vấn chính xác hơn
- Trả lời bằng tiếng Việt, markdown được phép"""


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "llama-3.3-70b-versatile"
    stream: Optional[bool] = True
    use_portfolio: Optional[bool] = True   # bật/tắt RAG
    filters: Optional[dict] = None         # structured filters từ UI


def _build_system_prompt(query: str, filters: Optional[dict] = None) -> str:
    """Hybrid search và inject kết quả vào system prompt."""
    try:
        results = hybrid_search(query, filters=filters, top_k=15)
        if not results:
            # Fallback: thử FTS không filter
            results = fts_search(query, top_k=10)
        context = format_properties_for_prompt(results)
    except Exception as e:
        print(f"[RAG] Search error: {e}")
        context = "⚠️ Không thể tải danh mục BĐS lúc này."

    return f"""{BASE_SYSTEM_PROMPT}

---
## DANH MỤC BĐS CÔNG TY (dữ liệu thực tế)

{context}
---

Hãy dựa vào danh mục trên để tư vấn. Nếu không có BĐS phù hợp, hãy nói thật và tư vấn chung về thị trường.
"""


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Lấy query từ tin nhắn cuối của user
        user_query = ""
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_query = msg.content
                break

        # Build system prompt với RAG
        if request.use_portfolio and user_query:
            system_content = _build_system_prompt(user_query, request.filters)
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
                        data = json.dumps({"content": delta.content, "done": False}, ensure_ascii=False)
                        yield f"data: {data}\n\n"
                yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            resp = client.chat.completions.create(
                model=request.model,
                messages=messages,
                stream=False,
                temperature=0.7,
                max_tokens=2048,
            )
            return {"content": resp.choices[0].message.content}

    except Exception as e:
        raise


@router.get("/models")
async def get_models():
    return {
        "models": [
            {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B (Nhanh & Thông minh)"},
            {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B (Siêu nhanh)"},
            {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B (Context dài)"},
            {"id": "gemma2-9b-it", "name": "Gemma 2 9B"},
        ]
    }
