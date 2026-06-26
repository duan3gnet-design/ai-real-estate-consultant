from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Real Estate Consultant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Bạn là một chuyên gia tư vấn bất động sản hàng đầu Việt Nam với hơn 15 năm kinh nghiệm.
Bạn am hiểu sâu sắc về:
- Thị trường bất động sản tại các thành phố lớn: Hà Nội, TP.HCM, Đà Nẵng, Hải Phòng...
- Các loại hình BĐS: căn hộ chung cư, nhà phố, biệt thự, đất nền, BĐS thương mại
- Pháp lý: sổ đỏ, sổ hồng, quy hoạch, thủ tục mua bán, sang nhượng
- Tài chính: vay ngân hàng, lãi suất, đòn bẩy tài chính, định giá BĐS
- Xu hướng đầu tư: phân tích tiềm năng tăng giá, rủi ro, dòng tiền cho thuê

Phong cách tư vấn:
- Chuyên nghiệp, tận tâm, trung thực
- Đưa ra phân tích cụ thể, số liệu thực tế
- Cảnh báo rủi ro khi cần thiết
- Hỏi thêm thông tin để tư vấn chính xác hơn
- Trả lời bằng tiếng Việt

Khi người dùng hỏi về BĐS cụ thể, hãy phân tích theo cấu trúc:
1. Nhận định chung về khu vực/dự án
2. Ưu điểm và nhược điểm
3. Mức giá tham khảo (nếu có thông tin)
4. Lời khuyên đầu tư
5. Các lưu ý pháp lý quan trọng"""


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "llama-3.3-70b-versatile"
    stream: Optional[bool] = True


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
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
                        data = json.dumps({"content": delta.content, "done": False})
                        yield f"data: {data}\n\n"
                yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            response = client.chat.completions.create(
                model=request.model,
                messages=messages,
                stream=False,
                temperature=0.7,
                max_tokens=2048,
            )
            return {"content": response.choices[0].message.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def get_models():
    return {
        "models": [
            {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B (Nhanh & Thông minh)"},
            {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B (Siêu nhanh)"},
            {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B (Context dài)"},
            {"id": "gemma2-9b-it", "name": "Gemma 2 9B"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
