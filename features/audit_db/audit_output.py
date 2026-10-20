"""Pembentukan respons dan spreadsheet hasil audit database."""

from io import BytesIO
from copy import copy
from pathlib import Path
from textwrap import wrap

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from features.audit_db.audit import Temuan
from features.audit_db.extract import ParsedDdl


TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "template" / "template.xlsx"
FIRST_DATA_ROW = 9


def buat_respons_audit(parsed_ddl: ParsedDdl, temuan: list[Temuan]) -> dict:
    return {
        "message": "Analisis standardisasi selesai.",
        "summary": {
            "table_count": len(parsed_ddl.tables),
            "column_count": parsed_ddl.column_count,
            "tables": sorted(parsed_ddl.tables),
        },
        "findings": [
            {
                "no": index,
                "nama_database": item.database_name,
                "nama_tabel": item.table_name,
                "objek_temuan": item.object_name,
                "aturan_playbook": item.playbook_rule,
                "uraian_ketidaksesuaian": item.nonconformity,
                "solusi": item.solution,
                "status": item.status,
                "catatan": item.note,
            }
            for index, item in enumerate(temuan, start=1)
        ],
    }


def _cell(value: str) -> str:
    return "'" + value if value.startswith(("=", "+", "-", "@")) else value


def buat_excel_temuan(database_name: str, temuan: list[Temuan]) -> bytes:
    workbook = load_workbook(TEMPLATE_PATH)
    sheet = workbook["MySQL - Setneg Point"]
    sheet.column_dimensions["H"].width = 55
    sheet.column_dimensions["I"].hidden = False
    sheet.column_dimensions["I"].width = sheet.column_dimensions["J"].width
    sheet.column_dimensions["J"].hidden = True
    sheet["I8"] = "Catatan"
    sheet["I8"]._style = copy(sheet["J8"]._style)
    sheet["J8"] = None

    sheet.data_validations.dataValidation.clear()

    last_row = FIRST_DATA_ROW + len(temuan) - 1
    for index, item in enumerate(temuan, start=1):
        row_number = FIRST_DATA_ROW + index - 1
        values = (
            index, _cell(database_name), _cell(item.table_name),
            _cell(item.object_name), _cell(item.playbook_rule),
            _cell(item.nonconformity), _cell(item.solution), _cell(item.note),
        )
        max_lines = 1
        for column, value in enumerate(values, start=2):
            source_column = column if column < 9 else 10
            cell = sheet.cell(row_number, column, value)
            cell._style = copy(sheet.cell(FIRST_DATA_ROW, source_column)._style)
            alignment = copy(cell.alignment)
            alignment.wrap_text = True
            cell.alignment = alignment
            width = max(1, int(sheet.column_dimensions[get_column_letter(column)].width) - 2)
            lines = sum(max(1, len(wrap(part, width=width))) for part in str(value).split("\n"))
            max_lines = max(max_lines, lines)
        sheet.row_dimensions[row_number].height = min(409.5, max(15.75, max_lines * 15))
        sheet.cell(row_number, 10).value = None

    rules = list(sheet.conditional_formatting["B9:J42"])
    del sheet.conditional_formatting["B9:J42"]
    for rule in rules:
        sheet.conditional_formatting.add(f"B9:I{max(last_row, FIRST_DATA_ROW)}", rule)

    total = len(temuan)
    selesai = sum(item.status == "Done" for item in temuan)
    sheet["B5"] = "TOTAL TEMUAN"
    sheet["E5"] = "TEMUAN AKTIF"
    sheet["G5"] = "TEMUAN SELESAI"
    sheet["I5"] = "TINGKAT PENYELESAIAN"
    sheet["B6"] = total
    sheet["E6"] = total - selesai
    sheet["G6"] = selesai
    sheet["I6"] = selesai / total if total else 0
    sheet["I6"].number_format = "0.0%"
    sheet.auto_filter.ref = f"B8:I{max(last_row, FIRST_DATA_ROW)}"
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
