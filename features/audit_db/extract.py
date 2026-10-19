"""Parsing DDL untuk fitur audit database."""

import re
from dataclasses import dataclass
from typing import Optional


class DdlValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Column:
    name: str
    definition: str


@dataclass(frozen=True)
class TableDefinition:
    columns: list[Column]
    constraints: list[str]
    options: str


@dataclass(frozen=True)
class ParsedDdl:
    tables: dict[str, TableDefinition]
    column_count: int
    database_name: Optional[str]


_IDENTIFIER = r"(?:`(?:``|[^`])+`|[A-Za-z_][A-Za-z0-9_]*)"
_CREATE_TABLE = re.compile(
    rf"^[ \t]*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
    rf"(?:(?P<database>{_IDENTIFIER})\s*\.\s*)?"
    rf"(?P<table>{_IDENTIFIER})\s*\(",
    re.IGNORECASE | re.MULTILINE,
)
_DEFINITION_COMMENT = re.compile(
    r"^[ \t]*--[ \t]*(?P<database>[A-Za-z_][A-Za-z0-9_]*)\."
    r"(?P<table>[A-Za-z_][A-Za-z0-9_]*)[ \t]+definition[ \t]*\r?$",
    re.IGNORECASE | re.MULTILINE,
)
_CONSTRAINT_START = re.compile(
    r"^(?:PRIMARY|UNIQUE|FOREIGN|KEY|INDEX|CONSTRAINT|CHECK|FULLTEXT|SPATIAL)\b",
    re.IGNORECASE,
)
_COLUMN_NAME = re.compile(rf"^(?P<name>{_IDENTIFIER})\s+", re.DOTALL)


def _unquote(identifier: str) -> str:
    return identifier[1:-1].replace("``", "`") if identifier.startswith("`") else identifier


def _split_definitions(sql: str) -> list[str]:
    parts = []
    start = 0
    depth = 0
    quote = None
    index = 0
    while index < len(sql):
        char = sql[index]
        if quote:
            if char == "\\" and quote in {"'", '"'}:
                index += 2
                continue
            if char == quote:
                if index + 1 < len(sql) and sql[index + 1] == quote:
                    index += 2
                    continue
                quote = None
        elif char in {"'", '"', "`"}:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(sql[start:index].strip())
            start = index + 1
        index += 1
    parts.append(sql[start:].strip())
    return [part for part in parts if part]


def _closing_parenthesis(sql: str, start: int) -> int:
    depth = 0
    quote = None
    index = start
    while index < len(sql):
        char = sql[index]
        if quote:
            if char == "\\" and quote in {"'", '"'}:
                index += 2
                continue
            if char == quote:
                if index + 1 < len(sql) and sql[index + 1] == quote:
                    index += 2
                    continue
                quote = None
        elif char in {"'", '"', "`"}:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    raise DdlValidationError("Pernyataan CREATE TABLE memiliki tanda kurung yang tidak lengkap.")


def parse_schema_ddl(content: bytes) -> ParsedDdl:
    try:
        sql = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise DdlValidationError("File SQL harus menggunakan encoding UTF-8.") from error

    tables: dict[str, TableDefinition] = {}
    database_names: set[str] = set()
    comments = list(_DEFINITION_COMMENT.finditer(sql))
    column_count = 0
    for match in _CREATE_TABLE.finditer(sql):
        table_name = _unquote(match.group("table"))
        database_name = _unquote(match.group("database")) if match.group("database") else None
        if not database_name:
            preceding = next((comment for comment in reversed(comments) if comment.end() <= match.start()), None)
            if preceding and preceding.group("table") == table_name:
                database_name = preceding.group("database")
        if database_name:
            database_names.add(database_name)
        if table_name in tables:
            raise DdlValidationError(f"Nama tabel '{table_name}' muncul lebih dari sekali.")
        closing = _closing_parenthesis(sql, match.end() - 1)
        definitions = _split_definitions(sql[match.end():closing])
        columns: list[Column] = []
        constraints: list[str] = []
        for definition in definitions:
            if _CONSTRAINT_START.match(definition):
                constraints.append(definition)
                continue
            column_match = _COLUMN_NAME.match(definition)
            if not column_match:
                raise DdlValidationError(f"Definisi kolom tidak dikenali pada tabel '{table_name}'.")
            columns.append(Column(_unquote(column_match.group("name")), definition))
        if not columns:
            raise DdlValidationError(f"Tabel '{table_name}' tidak memiliki kolom.")
        statement_end = sql.find(";", closing)
        options = sql[closing + 1:statement_end if statement_end != -1 else len(sql)].strip()
        tables[table_name] = TableDefinition(columns, constraints, options)
        column_count += len(columns)

    if not tables:
        raise DdlValidationError("File SQL tidak memiliki pernyataan CREATE TABLE.")
    if len(database_names) > 1:
        raise DdlValidationError("File SQL berisi lebih dari satu nama database.")
    return ParsedDdl(tables, column_count, next(iter(database_names), None))
