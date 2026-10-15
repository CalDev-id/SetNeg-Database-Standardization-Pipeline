import asyncio
from typing import Callable, Optional, Union

from utils.audit import LlmRuntime, audit_ddl
from utils.extract import ParsedDdl, parse_schema_ddl
from utils.audit_output import buat_excel_temuan, buat_respons_audit


async def process_schema_audit(
    sql_input: Union[bytes, ParsedDdl], output: str,
    on_batch_complete: Optional[Callable[[], None]] = None,
    runtime: Optional[LlmRuntime] = None,
):
    # 1. Extract SQL. Job Excel sudah divalidasi saat upload.
    if isinstance(sql_input, ParsedDdl):
        parsed_ddl = sql_input
    else:
        parsed_ddl = await asyncio.to_thread(parse_schema_ddl, sql_input)

    # 2. Audit tabel dan kolom per batch.
    temuan = await audit_ddl(parsed_ddl, runtime=runtime, on_batch_complete=on_batch_complete)

    # 3. Buat output sesuai endpoint.
    if output == "excel":
        return await asyncio.to_thread(buat_excel_temuan, parsed_ddl.database_name or "-", temuan)
    if output == "json":
        return buat_respons_audit(parsed_ddl, temuan)
    raise ValueError("Format output tidak dikenal.")
