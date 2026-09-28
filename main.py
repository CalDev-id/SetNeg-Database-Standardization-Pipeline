from fastapi import FastAPI
from routes.analyses import router as analyses_router

app = FastAPI(
    title="Database Standardization API",
    version="0.1.0",
    description="API untuk analisis standardisasi nama tabel dan kolom database.",
)

app.include_router(analyses_router, prefix="/api/v1/analyses", tags=["analyses"])


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Database Standardization API is running."}
