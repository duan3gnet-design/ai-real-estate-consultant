# 🏠 AI Tư Vấn Bất Động Sản

Desktop app tư vấn bất động sản thông minh, được xây dựng với **Electron + React/Vite + FastAPI + Groq**.

## 🏗️ Cấu trúc Project

```
ai-real-estate-consultant/
├── backend/
│   ├── main.py              # FastAPI server + Groq streaming
│   ├── requirements.txt
│   └── .env                 # GROQ_API_KEY
├── electron/
│   ├── main.js              # Electron main process
│   └── preload.js           # Context bridge
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TitleBar.jsx     # Custom title bar
│   │   │   ├── Sidebar.jsx      # Session list + model selector
│   │   │   ├── MessageList.jsx  # Chat messages + welcome screen
│   │   │   └── ChatInput.jsx    # Input với auto-resize
│   │   ├── hooks/
│   │   │   ├── useChat.js       # Chat state + streaming logic
│   │   │   └── useUtils.js      # Auto-resize, scroll, backend status
│   │   ├── services/
│   │   │   └── api.js           # API calls + SSE streaming
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   └── package.json
├── package.json             # Root (Electron + scripts)
├── start-backend.bat        # Chỉ chạy backend
└── start-dev.bat            # Chạy cả hai (dev mode)
```

## ⚡ Cài đặt & Chạy

### 1. Cấu hình Groq API Key

```bash
# Sửa file backend/.env
GROQ_API_KEY=your_groq_api_key_here
```

Lấy API key miễn phí tại: https://console.groq.com

### 2. Cài đặt dependencies

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

### 3. Chạy dev mode

**Cách 1 - Script tự động (Windows):**
```bash
start-dev.bat
```

**Cách 2 - Thủ công:**
```bash
# Terminal 1: Backend
cd backend && python main.py

# Terminal 2: Electron + Vite
npm run dev
```

## 🤖 Tính năng

- **Chat streaming** với AI tư vấn BĐS chuyên sâu
- **Nhiều model** Groq: Llama 3.3 70B, Llama 3.1 8B, Mixtral 8x7B
- **Quản lý session** chat với lịch sử
- **Markdown rendering** với bảng, in đậm, danh sách
- **Custom title bar** (frameless window)
- **Backend health check** tự động

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop | Electron 33 |
| Frontend | React 18 + Vite 5 |
| Backend | FastAPI + Uvicorn |
| AI | Groq API (llama-3.3-70b) |
| Streaming | Server-Sent Events (SSE) |
