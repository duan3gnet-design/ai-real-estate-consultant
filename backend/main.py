from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import chat, properties, consultations


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Main] Initializing database...")
    init_db()
    print("[Main] Server ready at http://127.0.0.1:8765")
    yield
    print("[Main] Shutting down.")


app = FastAPI(
    title="AI Real Estate Consultant API",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(properties.router)
app.include_router(consultations.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
