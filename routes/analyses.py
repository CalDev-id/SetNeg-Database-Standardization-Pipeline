from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from pipelines.csv_input import CsvValidationError, parse_schema_csv
from pipelines.report import create_completed_report
from pipelines.standardize import StandardizationError, standardize_csv

router = APIRouter()
MAX_UPLOAD_SIZE_BYTES = 1_000_000
MAX_TABLES_PER_REQUEST = 10


class AnalysisSummary(BaseModel):
    table_count: int = Field(ge=1)
    column_count: int = Field(ge=1)
    tables: list[str]


class AnalysisFinding(BaseModel):
    no: int = Field(ge=1)
    nama_tabel: str
    objek_temuan: str
    aturan_playbook: str
    uraian_ketidaksesuaian: str
    solusi: str
    confidence: str


class AnalysisResponse(BaseModel):
    message: str
    summary: AnalysisSummary
    findings: list[AnalysisFinding]


@router.post("", response_model=AnalysisResponse)
async def create_analysis(file: UploadFile = File(...)) -> AnalysisResponse:
    """Menerima CSV struktur tabel dan mengembalikan hasil standardisasi."""
    if file.content_type not in {"text/csv", "application/csv", "application/vnd.ms-excel"}:
        raise HTTPException(status_code=415, detail="File harus berformat CSV.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Ukuran CSV maksimal 1 MB.")

    try:
        parsed_csv = parse_schema_csv(content)
    except CsvValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    if len(parsed_csv.tables) > MAX_TABLES_PER_REQUEST:
        raise HTTPException(
            status_code=422,
            detail=f"CSV maksimal berisi {MAX_TABLES_PER_REQUEST} tabel per request.",
        )

    try:
        findings = await standardize_csv(parsed_csv)
    except StandardizationError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error

    return AnalysisResponse(**create_completed_report(parsed_csv, findings))
