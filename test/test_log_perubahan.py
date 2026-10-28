import asyncio
import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from api.routes import data_dictionary as routes
from features.data_dictionary import pipeline
from features.data_dictionary.log_perubahan import (
    LogPerubahanError, PROMPT_LOG_PERUBAHAN, build_log_perubahan, count_log_batches,
)


def dictionaries(column_count=1):
    old = {"records": {"kolom": {
        f"field_{number}": {"tipe_data": "INT", "key": "", "comment": "Nilai."}
        for number in range(1, column_count + 1)
    }}}
    new = {"record": {"kolom_baru": [
        {"nama_kolom": name, "no_kolom": number, "tipe_data": "INT", "log": {"no_lama": number}}
        for number, name in enumerate(old["records"]["kolom"], 1)
    ]}}
    return old, new


class FakeRuntime:
    def __init__(self, invalid=None):
        self.calls = []
        self.invalid = invalid

    def generate_response(self, system, user):
        assert system == PROMPT_LOG_PERUBAHAN
        batch, _ = json.JSONDecoder().raw_decode(user[user.index("{"):])
        self.calls.append(batch)
        rows = []
        for source in batch["dictionary_new"]:
            added = source["no_lama_sumber"] is None
            rows.append({
                "no_baru": source["no_baru"], "no_lama": source["no_lama_sumber"],
                "nama_tabel": source["nama_tabel"], "jenis_perubahan": "Baru" if added else "Direvisi",
                "objek_temuan": "Standard Field Audit Trail" if added else "Nama tabel",
                "aturan_playbook": "4. Standard Field Audit Trail" if added else "2b. Nama tabel",
                "posisi_sisipan": "Kolom pertama" if added else None,
                "uraian_baru": "Kolom ditambahkan sesuai temuan." if added else None,
            })
        if self.invalid:
            self.invalid(rows, len(self.calls))
        return json.dumps({"log_perubahan": rows})


class LogPerubahanTests(unittest.IsolatedAsyncioTestCase):
    async def test_small_log_remainder_uses_one_batch(self):
        self.assertEqual(count_log_batches(dictionaries(29)[1]), 1)
        self.assertEqual(count_log_batches(dictionaries(30)[1]), 1)
        self.assertEqual(count_log_batches(dictionaries(31)[1]), 2)

    async def test_removed_column_is_logged_without_asking_llm_or_losing_old_mapping(self):
        old, new = dictionaries(2)
        new["record"]["kolom_baru"].pop()
        new["record"]["kolom_dihapus"] = [{"no_lama": 2, "alasan": "Atribut redundant."}]
        new["record"]["kolom_baru"][0]["log"].update({
            "jenis_perubahan": "Direvisi", "objek_temuan": "Nama tabel",
            "aturan_playbook": "2b. Nama tabel",
        })
        findings = [{"nama_tabel": "records", "objek_temuan": "Nama tabel"}]
        normalization = [{
            "Nama Tabel": "records", "Kolom Terdampak": "`field_2`",
            "Objek Temuan": "3NF - Duplikasi", "Tahap Normalisasi": "3NF",
            "Solusi Normalisasi": "Hapus `field_2` dari rancangan.",
            "Tabel Baru Usulan": "-",
        }]
        runtime = FakeRuntime()
        result = await build_log_perubahan(
            old, new, findings, runtime, normalization_findings=normalization,
        )
        self.assertEqual(runtime.calls, [])
        self.assertEqual(result["log_perubahan"][1]["no_baru"], None)
        self.assertEqual(result["log_perubahan"][1]["no_lama"], 2)
        self.assertEqual(result["log_perubahan"][1]["jenis_perubahan"], "Dihapus dari rancangan")
        self.assertEqual(result["log_perubahan"][1]["objek_temuan"], "3NF - Duplikasi")
        self.assertIn("tetap dipertahankan", result["log_perubahan"][1]["uraian_baru"])

    async def test_audit_backed_removed_column_uses_audit_label(self):
        old, new = dictionaries(2)
        new["record"]["kolom_baru"].pop()
        new["record"]["kolom_dihapus"] = [{"no_lama": 2, "alasan": "Redundan."}]
        new["record"]["kolom_baru"][0]["log"].update({
            "jenis_perubahan": "Direvisi", "objek_temuan": "Nama tabel",
            "aturan_playbook": "2b. Nama tabel",
        })
        findings = [
            {"nama_tabel": "records", "objek_temuan": "Nama tabel", "aturan_playbook": "2b. Nama tabel"},
            {"nama_tabel": "records", "objek_temuan": "Kolom field_2 redundan",
             "aturan_playbook": "Aturan relasi", "solusi": "Hapus `field_2` dari rancangan."},
        ]
        result = await build_log_perubahan(old, new, findings, FakeRuntime())
        removed = result["log_perubahan"][1]
        self.assertEqual(removed["objek_temuan"], "Kolom field_2 redundan")
        self.assertEqual(removed["aturan_playbook"], "Aturan relasi")

    async def test_complete_dictionary_logs_skip_llm(self):
        old, new = dictionaries(23)
        for column in new["record"]["kolom_baru"]:
            column["log"].update({
                "jenis_perubahan": "Direvisi",
                "objek_temuan": "Nama tabel",
                "aturan_playbook": "2b. Nama tabel",
                "posisi_sisipan": None,
                "uraian_baru": None,
            })
        runtime = FakeRuntime()
        progress = []
        findings = [{"nama_tabel": "records", "objek_temuan": "Nama tabel"}]
        result = await build_log_perubahan(old, new, findings, runtime, lambda: progress.append(True))
        self.assertEqual(len(result["log_perubahan"]), 23)
        self.assertEqual(runtime.calls, [])
        self.assertEqual(len(progress), 1)

    async def test_only_incomplete_log_batch_uses_llm(self):
        old, new = dictionaries(31)
        for column in new["record"]["kolom_baru"]:
            column["log"].update({
                "jenis_perubahan": "Direvisi",
                "objek_temuan": "Nama tabel",
                "aturan_playbook": "2b. Nama tabel",
                "posisi_sisipan": None,
                "uraian_baru": None,
            })
        new["record"]["kolom_baru"][20]["log"]["aturan_playbook"] = "-"
        runtime = FakeRuntime()
        progress = []
        findings = [{"nama_tabel": "records", "objek_temuan": "Nama tabel"}]
        result = await build_log_perubahan(old, new, findings, runtime, lambda: progress.append(True))
        self.assertEqual(len(result["log_perubahan"]), 31)
        self.assertEqual(len(runtime.calls), 1)
        self.assertEqual(len(runtime.calls[0]["dictionary_new"]), 11)
        self.assertEqual(len(progress), 2)

    async def test_log_without_supporting_finding_uses_llm(self):
        old, new = dictionaries()
        new["record"]["kolom_baru"][0]["log"].update({
            "jenis_perubahan": "Direvisi",
            "objek_temuan": "Temuan tidak ada",
            "aturan_playbook": "Aturan tidak ada",
        })
        runtime = FakeRuntime()
        await build_log_perubahan(old, new, [], runtime)
        self.assertEqual(len(runtime.calls), 1)

    async def test_global_numbers_across_batches_and_new_tables(self):
        old, new = dictionaries(29)
        new["record"]["kolom_baru"].append({
            "nama_kolom": "created_at", "no_kolom": 30, "log": {"no_lama": None},
        })
        new["metadata_database"] = {"kolom_baru": [
            {"nama_kolom": "metadata_database_id", "no_kolom": 1, "log": {"no_lama": None}},
        ]}
        findings = [{"nama_tabel": "records", "objek_temuan": "Nama tabel", "solusi": "record"}]
        runtime = FakeRuntime()
        progress = []
        snapshot = copy.deepcopy((old, new, findings))
        result = await build_log_perubahan(old, new, findings, runtime, lambda: progress.append(True))
        rows = result["log_perubahan"]
        self.assertEqual([row["no_baru"] for row in rows], list(range(1, 32)))
        self.assertEqual([row["no_lama"] for row in rows], list(range(1, 30)) + [None, None])
        self.assertEqual(len(runtime.calls), 2)
        self.assertEqual(len(progress), 2)
        self.assertEqual(runtime.calls[0]["tabel_context"]["record"]["temuan_audit"], findings)
        self.assertEqual(
            {row["nama_tabel"] for row in runtime.calls[-1]["dictionary_new"]},
            {"record", "metadata_database"},
        )
        self.assertTrue(runtime.calls[-1]["tabel_context"]["metadata_database"]["tabel_baru"])
        self.assertEqual(len(rows[0]), 8)
        self.assertEqual((old, new, findings), snapshot)

    async def test_incomplete_response_is_completed_from_dictionary(self):
        old, new = dictionaries()
        runtime = FakeRuntime(lambda rows, call: rows.clear() if call == 1 else None)
        result = await build_log_perubahan(old, new, [], runtime)
        self.assertEqual(len(runtime.calls), 1)
        self.assertEqual(len(result["log_perubahan"]), 1)

    async def test_invalid_mapping_is_replaced_from_dictionary(self):
        old, new = dictionaries()
        runtime = FakeRuntime(lambda rows, call: rows[0].update(no_lama=999))
        result = await build_log_perubahan(old, new, [], runtime)
        self.assertEqual(len(runtime.calls), 1)
        self.assertEqual(result["log_perubahan"][0]["no_lama"], 1)

    async def test_existing_row_insertion_details_are_ignored(self):
        old, new = dictionaries()
        runtime = FakeRuntime(lambda rows, call: rows[0].update(posisi_sisipan="Kolom pertama"))
        result = await build_log_perubahan(old, new, [], runtime)
        self.assertIsNone(result["log_perubahan"][0]["posisi_sisipan"])

    async def test_incomplete_dictionary_is_rejected_before_llm(self):
        old, new = dictionaries(2)
        new["record"]["kolom_baru"].pop()
        runtime = FakeRuntime()
        with self.assertRaisesRegex(LogPerubahanError, "belum tercakup"):
            await build_log_perubahan(old, new, [], runtime)
        self.assertEqual(runtime.calls, [])

    async def test_endpoint_rejects_dictionary_from_other_audit(self):
        audit = SimpleNamespace(status="completed", audit_result={"findings": []})
        old = SimpleNamespace(status="completed", result={}, audit_job_id="audit-a")
        new = SimpleNamespace(status="completed", result={}, audit_job_id="audit-b")
        data = routes.LogPerubahanRequest(audit_job_id="audit-a", normalization_job_id="normal",
                                           old_dictionary_job_id="old", new_dictionary_job_id="new")
        with patch.object(routes, "find_spreadsheet_job", return_value=audit), \
             patch.object(routes, "find_normalization_job", return_value=SimpleNamespace(status="completed", audit_job_id="audit-a", findings=[])), \
             patch.object(routes, "find_old_dictionary_job", return_value=old), \
             patch.object(routes, "find_new_dictionary_job", return_value=new):
            with self.assertRaises(HTTPException) as caught:
                await routes.create_log_perubahan(data, None)
        self.assertEqual(caught.exception.status_code, 422)

    async def test_endpoint_runs_job_and_returns_complete_log(self):
        old_result, new_result = dictionaries()
        audit = SimpleNamespace(status="completed", audit_result={"findings": []})
        old = SimpleNamespace(status="completed", result=old_result, audit_job_id="audit")
        new = SimpleNamespace(status="completed", result=new_result, audit_job_id="audit")
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(audit_semaphore=asyncio.Semaphore(1))))
        data = routes.LogPerubahanRequest(audit_job_id="audit", normalization_job_id="normal",
                                           old_dictionary_job_id="old", new_dictionary_job_id="new")
        with patch.object(routes, "find_spreadsheet_job", return_value=audit), \
             patch.object(routes, "find_normalization_job", return_value=SimpleNamespace(status="completed", audit_job_id="audit", findings=[])), \
             patch.object(routes, "find_old_dictionary_job", return_value=old), \
             patch.object(routes, "find_new_dictionary_job", return_value=new), \
             patch.object(pipeline, "get_runtime", return_value=FakeRuntime()), \
             patch.dict(pipeline._log_jobs, clear=True):
            created = await routes.create_log_perubahan(data, request)
            await asyncio.gather(*list(pipeline._tasks))
            status = await routes.get_log_perubahan(created["job_id"])
        self.assertEqual(status["status"], "completed")
        self.assertEqual(status["completed_batches"], status["total_batches"])
        self.assertEqual(status["result"]["log_perubahan"][0]["nama_tabel"], "record")


if __name__ == "__main__":
    unittest.main()
