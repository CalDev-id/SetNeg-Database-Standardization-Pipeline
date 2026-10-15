import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routes.audit import router as audit_router

MAX_PARALLEL_AUDITS = 2


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.audit_semaphore = asyncio.Semaphore(MAX_PARALLEL_AUDITS)
    yield


app = FastAPI(
    title="Database Schema Audit API",
    version="0.1.0",
    description="API untuk audit struktur database berdasarkan playbook.",
    lifespan=lifespan,
)

app.include_router(audit_router, prefix="/api/v1/audit", tags=["audit"])
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")


@app.get("/")
async def read_root() -> FileResponse:
    return FileResponse(Path(__file__).resolve().parent / "static" / "index.html")


@app.get("/health")
async def read_health() -> dict[str, str]:
    return {"message": "Database Schema Audit API is running."}
