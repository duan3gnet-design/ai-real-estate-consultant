from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.es_client import init_es
from app.routers import chat, properties, consultations


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Main] Connecting to Elasticsearch...")
    init_es()
    print("[Main] Server ready at http://127.0.0.1:8765")
    yield
    print("[Main] Shutting down.")


app = FastAPI(
    title="AI Real Estate Consultant API",
    version="4.0.0",
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
    from app.es_client import get_es
    try:
        es_health = get_es().cluster.health()
        return {"status": "ok", "version": "4.0.0", "elasticsearch": es_health["status"]}
    except Exception as e:
        return {"status": "error", "version": "4.0.0", "elasticsearch_error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
