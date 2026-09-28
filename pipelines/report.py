from pipelines.csv_input import ParsedCsv
from pipelines.standardize import Finding


def create_completed_report(parsed_csv: ParsedCsv, findings: list[Finding]) -> dict:
    return {
        "message": "Analisis standardisasi selesai.",
        "summary": {
            "table_count": len(parsed_csv.tables),
            "column_count": parsed_csv.column_count,
            "tables": sorted(parsed_csv.tables),
        },
        "findings": [
            {
                "no": index,
                "nama_tabel": finding.table_name,
                "objek_temuan": finding.object_name,
                "aturan_playbook": finding.playbook_rule,
                "uraian_ketidaksesuaian": finding.nonconformity,
                "solusi": finding.solution,
                "confidence": finding.confidence,
            }
            for index, finding in enumerate(findings, start=1)
        ],
    }
