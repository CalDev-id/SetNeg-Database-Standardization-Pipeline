import csv
from dataclasses import dataclass
from io import StringIO


REQUIRED_COLUMNS = {"Nama Tabel", "Nama Kolom", "Tipe data"}


class CsvValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Column:
    name: str
    data_type: str


@dataclass(frozen=True)
class ParsedCsv:
    tables: dict[str, list[Column]]
    column_count: int


def parse_schema_csv(content: bytes) -> ParsedCsv:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise CsvValidationError("CSV harus menggunakan encoding UTF-8.") from error

    reader = csv.DictReader(StringIO(text))
    fieldnames = set(reader.fieldnames or [])
    missing_columns = REQUIRED_COLUMNS - fieldnames
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise CsvValidationError(f"Header wajib tidak ditemukan: {missing}.")

    tables: dict[str, list[Column]] = {}
    row_count = 0
    for line_number, row in enumerate(reader, start=2):
        table_name = (row.get("Nama Tabel") or "").strip()
        column_name = (row.get("Nama Kolom") or "").strip()
        data_type = (row.get("Tipe data") or "").strip()
        if not all((table_name, column_name, data_type)):
            raise CsvValidationError(
                f"Baris {line_number} harus memiliki Nama Tabel, Nama Kolom, dan Tipe data."
            )
        tables.setdefault(table_name, []).append(
            Column(name=column_name, data_type=data_type)
        )
        row_count += 1

    if row_count == 0:
        raise CsvValidationError("CSV tidak memiliki data untuk dianalisis.")

    return ParsedCsv(tables=tables, column_count=row_count)
