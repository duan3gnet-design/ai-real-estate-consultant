# 🏠 AI Tư Vấn Bất Động Sản

Desktop app tư vấn bất động sản thông minh, được xây dựng với **Electron + React/Vite + FastAPI + Elasticsearch + Groq**.

AI tư vấn dựa trên **RAG hybrid search** (full-text + vector) trên 2 nguồn dữ liệu công ty:
- **Danh mục bất động sản** (có thể lên đến hàng triệu BĐS)
- **Lịch sử các buổi tư vấn trước** (transcript + kết quả CRM) để học từ kinh nghiệm thực tế

## 🏗️ Cấu trúc Project

```
ai-real-estate-consultant/
├── backend/
│   ├── app/
│   │   ├── es_client.py         # Elasticsearch client + index mappings
│   │   ├── embedding.py         # SentenceTransformer embedding service
│   │   ├── models.py            # Pydantic models (Property...)
│   │   ├── routers/
│   │   │   ├── chat.py              # /chat — RAG streaming với Groq
│   │   │   ├── properties.py        # /properties — CRUD + import + stats
│   │   │   └── consultations.py     # /consultations — CRUD + transcript + AI analysis
│   │   └── services/
│   │       ├── search.py                # Hybrid search (FTS + vector + RRF) cho BĐS
│   │       ├── property_service.py      # CRUD BĐS trên Elasticsearch
│   │       ├── consultation_search.py   # Hybrid search cho lịch sử tư vấn
│   │       └── consultation_service.py  # CRUD + import + analytics tư vấn
│   ├── main.py               # FastAPI entrypoint
│   ├── requirements.txt
│   └── .env                  # GROQ_API_KEY, ELASTICSEARCH_URL
├── electron/
│   ├── main.js                # Electron main process (tự spawn backend Python)
│   └── preload.js             # Context bridge
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TitleBar.jsx                 # Custom frameless title bar
│   │   │   ├── Sidebar.jsx                  # Session list + model selector
│   │   │   ├── MessageList.jsx              # Chat messages + welcome screen
│   │   │   ├── ChatInput.jsx                # Input với auto-resize
│   │   │   ├── SaveToConsultationModal.jsx  # Lưu chat hiện tại → lịch sử tư vấn
│   │   │   ├── PropertyManager.jsx          # Bảng quản lý danh mục BĐS
│   │   │   ├── PropertyForm.jsx             # Form thêm/sửa BĐS (30+ trường)
│   │   │   ├── ConsultationManager.jsx      # Bảng quản lý lịch sử tư vấn
│   │   │   ├── ConsultationForm.jsx         # Form thêm/sửa buổi tư vấn
│   │   │   ├── TranscriptModal.jsx          # Xem/sửa transcript buổi tư vấn
│   │   │   ├── AnalysisModal.jsx            # Kết quả AI phân tích chất lượng
│   │   │   └── ImportModal.jsx              # Import CSV/JSON (drag & drop)
│   │   ├── hooks/
│   │   │   ├── useChat.js           # Chat state + streaming logic
│   │   │   ├── useProperties.js     # State quản lý danh mục BĐS
│   │   │   └── useUtils.js          # Auto-resize, scroll, backend status
│   │   ├── services/
│   │   │   └── api.js               # Tất cả API calls (chat, properties, consultations)
│   │   ├── constants.js             # Enums, màu sắc, format helpers
│   │   ├── App.jsx                  # 3 tabs: Tư vấn AI | Danh mục BĐS | Lịch sử Tư vấn
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   └── package.json
├── docker-compose.yml         # Elasticsearch + Kibana (local)
├── package.json               # Root (Electron + scripts)
├── start-backend.bat          # Chỉ chạy backend
└── start-dev.bat              # Chạy cả backend + Electron (dev mode)
```

## ⚡ Cài đặt & Chạy

### 1. Khởi động Elasticsearch (Docker)

```bash
docker compose up -d
```

Kiểm tra ES đã chạy: mở `http://localhost:9200` (sẽ thấy thông tin cluster).
Kibana (tùy chọn, để xem dữ liệu trực quan): `http://localhost:5601`.

### 2. Cấu hình `.env`

Sửa file `backend/.env`:

```bash
GROQ_API_KEY=your_groq_api_key_here
ELASTICSEARCH_URL=http://localhost:9200
```

Lấy Groq API key miễn phí tại: https://console.groq.com

### 3. Cài đặt dependencies

```bash
# Root dependencies (Electron)
npm install

# Frontend dependencies
cd frontend && npm install

# Backend dependencies (Python)
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

> Lần đầu chạy backend sẽ tự động tải model embedding `paraphrase-multilingual-MiniLM-L12-v2` (~120MB) và tạo các Elasticsearch index.

### 4. Chạy dev mode

**Cách 1 — Script tự động (Windows):**
```bash
start-dev.bat
```

**Cách 2 — Thủ công:**
```bash
# Terminal 1: Elasticsearch (nếu chưa chạy)
docker compose up -d

# Terminal 2: Backend
cd backend && python main.py

# Terminal 3: Electron + Vite
npm run dev
```

## 🤖 Tính năng

### Tư vấn AI (RAG Hybrid Search)
- Chat streaming với AI tư vấn BĐS chuyên sâu (Groq: Llama 3.3 70B, Llama 3.1 8B, Mixtral 8x7B)
- AI tự động tìm kiếm **danh mục BĐS phù hợp** và **kinh nghiệm từ các buổi tư vấn tương tự trước đó**, inject vào context để tư vấn chính xác hơn
- Hybrid search = full-text (Elasticsearch `multi_match`) + vector search (Elasticsearch `knn`) merge bằng **Reciprocal Rank Fusion (RRF)** — hoạt động hiệu quả dù danh mục có hàng triệu bản ghi
- Lưu cuộc trò chuyện hiện tại thành 1 buổi tư vấn vào lịch sử, tự động chuyển đổi tin nhắn thành transcript

### Danh mục Bất động sản
- CRUD đầy đủ: 30+ trường (vị trí, diện tích, giá, pháp lý, tiện ích, liên hệ...)
- Bộ lọc đa chiều: loại BĐS, trạng thái, khu vực, giá, diện tích, số phòng ngủ, pháp lý
- Import hàng loạt từ CSV/JSON (tự động map tên cột linh hoạt, hỗ trợ tiếng Anh/Việt)
- Thống kê: tổng số, theo loại, theo khu vực, giá trung bình

### Lịch sử Tư vấn
- Quản lý từng buổi tư vấn: thông tin khách hàng, nhu cầu, ngân sách, kết quả (Chốt giao dịch / Hẹn lại / Từ chối...)
- Lưu transcript chi tiết (upload file .txt thô, tự động nhận diện người nói)
- **AI phân tích chất lượng** mỗi buổi tư vấn: chấm điểm 5 tiêu chí (khám phá nhu cầu, trình bày sản phẩm, xử lý phản đối, kỹ năng chốt sale, chuyên nghiệp), liệt kê điểm mạnh/yếu, gợi ý cải thiện
- Thống kê: tỷ lệ chốt giao dịch, thời lượng trung bình, hiệu suất theo nhân viên, lý do từ chối phổ biến

### UI/UX
- Custom title bar (frameless window), theme navy/gold sang trọng
- Markdown rendering với bảng, in đậm, danh sách trong câu trả lời AI
- Backend + Elasticsearch health check tự động

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop | Electron 33 |
| Frontend | React 18 + Vite 5 |
| Backend | FastAPI + Uvicorn |
| Database / Search | Elasticsearch 8.15 (full-text + vector + structured CRUD) |
| Embedding | sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`) |
| AI | Groq API (Llama 3.3 70B / 3.1 8B, Mixtral 8x7B) |
| Streaming | Server-Sent Events (SSE) |
| Infra | Docker Compose (Elasticsearch + Kibana) |

## 📡 API Endpoints chính

| Method | Path | Mô tả |
|--------|------|------|
| POST | `/chat` | Chat streaming với RAG (BĐS + lịch sử tư vấn) |
| GET/POST | `/properties` | List/tạo BĐS |
| GET/PUT/DELETE | `/properties/{id}` | Chi tiết/sửa/xóa BĐS |
| POST | `/properties/import/csv`, `/import/json` | Import hàng loạt |
| GET | `/properties/stats` | Thống kê danh mục |
| GET/POST | `/consultations` | List/tạo buổi tư vấn |
| POST | `/consultations/{id}/transcript` | Lưu transcript |
| POST | `/consultations/{id}/transcript/text` | Upload transcript dạng text thô |
| POST | `/consultations/analyze` | AI phân tích chất lượng buổi tư vấn |
| GET | `/consultations/stats` | Thống kê hiệu suất tư vấn |
| GET | `/health` | Health check backend + Elasticsearch |

## 🔄 Migrate dữ liệu cũ (nếu có)

Nếu trước đây dùng SQLite + ChromaDB, dữ liệu cũ nằm ở `backend/data/realestate.db` và `backend/data/chroma/`. App hiện tại không tự động đọc các file này — cần migrate thủ công bằng script riêng nếu muốn giữ dữ liệu cũ (liên hệ để được hỗ trợ viết script `migrate_sqlite_to_es.py`).
