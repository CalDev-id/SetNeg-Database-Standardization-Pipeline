import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes.audit_db import router as audit_router
from api.routes.data_dictionary import router as data_dictionary_router
from api.routes.ddl_standard import router as ddl_standard_router

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
app.include_router(data_dictionary_router, prefix="/api/v1/data-dictionary", tags=["data-dictionary"])
app.include_router(ddl_standard_router, prefix="/api/v1/ddl-standard", tags=["ddl-standard"])
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")


@app.get("/")
async def read_root() -> FileResponse:
    return FileResponse(Path(__file__).resolve().parent / "static" / "index.html")


@app.get("/health")
async def read_health() -> dict[str, str]:
    return {"message": "Database Schema Audit API is running."}
