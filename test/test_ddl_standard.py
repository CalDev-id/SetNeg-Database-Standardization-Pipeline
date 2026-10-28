import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from api.routes import ddl_standard as routes
from features.ddl_standard import pipeline as ddl_pipeline
from features.ddl_standard.ddl_standard import DdlStandardError, build_ddl_standard


SOURCE_DDL = b"CREATE TABLE `records` (`id` int NOT NULL, `name` varchar(50), PRIMARY KEY (`id`));"
OLD = {"records": {"kolom": {"id": {}, "name": {}}}}
NEW = {"record": {"jenis_tabel": "Transaksi/relasi", "kolom_baru": [
    {"no_kolom": 1, "nama_kolom": "record_id", "log": {"no_lama": 1}},
    {"no_kolom": 2, "nama_kolom": "name", "log": {"no_lama": 2}},
]}}


class FakeRuntime:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def generate_response(self, system, prompt):
        payload, _ = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])
        self.calls.append(payload)
        return json.dumps(self.result)


class DdlStandardTests(unittest.IsolatedAsyncioTestCase):
    async def test_job_log_records_create_retry_and_alter(self):
        class Runtime:
            create_calls = 0

            def generate_response(self, system, _prompt):
                if "instalasi baru" in system:
                    self.create_calls += 1
                    if self.create_calls == 1:
                        return json.dumps({"ddl_create": ""})
                    return json.dumps({"ddl_create": "CREATE TABLE `record` (`record_id` BIGINT, `name` VARCHAR(50));"})
                return json.dumps({"ddl_alter": "ALTER TABLE `records` RENAME TO `record`;"})

        with patch.dict(ddl_pipeline._jobs, clear=True), \
             patch.object(ddl_pipeline, "get_runtime", return_value=Runtime()):
            job_id = await ddl_pipeline.start_ddl_standard_job(
                SOURCE_DDL, OLD, NEW, "telkom", asyncio.Semaphore(1), "audit",
            )
            await asyncio.gather(*list(ddl_pipeline._tasks))
            job = ddl_pipeline.find_ddl_standard_job(job_id)
            self.assertEqual(job.status, "completed")
            self.assertEqual([(event["kind"], event["step"]) for event in job.process_events], [
                ("started", "create"), ("retry", "create"), ("completed", "create"),
                ("started", "alter"), ("completed", "alter"),
            ])
            with patch.object(routes, "find_ddl_standard_job", return_value=job):
                status = await routes.get_ddl_standard(job_id)
            self.assertEqual(status["process_events"], job.process_events)

    async def test_job_log_records_failed_create(self):
        class Runtime:
            def generate_response(self, _system, _prompt):
                return json.dumps({"error": "referensi view tidak cukup"})

        with patch.dict(ddl_pipeline._jobs, clear=True), \
             patch.object(ddl_pipeline, "get_runtime", return_value=Runtime()):
            job_id = await ddl_pipeline.start_ddl_standard_job(
                SOURCE_DDL, OLD, NEW, "telkom", asyncio.Semaphore(1), "audit",
            )
            await asyncio.gather(*list(ddl_pipeline._tasks))
            job = ddl_pipeline.find_ddl_standard_job(job_id)
            self.assertEqual(job.status, "failed")
            self.assertEqual(job.process_events[-1]["kind"], "failed")
            self.assertEqual(job.process_events[-1]["step"], "create")
            self.assertIn("referensi view tidak cukup", job.process_events[-1]["message"])

    async def test_removed_design_column_stays_in_physical_table(self):
        new = {"record": {"jenis_tabel": "Transaksi/relasi",
                          "kolom_dihapus": [{"no_lama": 2, "alasan": "Redundan."}],
                          "kolom_baru": [NEW["record"]["kolom_baru"][0]]}}
        runtime = FakeRuntime({
            "ddl_alter": "RENAME TABLE `records` TO `record`;",
            "ddl_create": "CREATE TABLE `record` (`record_id` BIGINT NOT NULL);",
        })
        result = await build_ddl_standard(SOURCE_DDL, OLD, new, runtime)
        self.assertIn("`name`", result["ddl_alter"])
        self.assertIn("tetap dipertahankan secara fisik", result["ddl_alter"])
        self.assertNotIn("DROP COLUMN", result["ddl_alter"])
        self.assertIn("`record_id` BIGINT NOT NULL", result["ddl_create"])
        self.assertNotIn("kolom_dihapus", runtime.calls[0]["objek"][0]["dictionary_new"])
        self.assertEqual(runtime.calls[1]["objek"][0]["dictionary_new"]["kolom_dihapus"][0]["no_lama"], 2)

        bad = FakeRuntime({
            "ddl_alter": "ALTER TABLE `records` CHANGE COLUMN `name` `legacy_name` VARCHAR(50);",
            "ddl_create": "CREATE TABLE `record` (`record_id` BIGINT NOT NULL);",
        })
        with self.assertRaisesRegex(DdlStandardError, "wajib dipertahankan"):
            await build_ddl_standard(SOURCE_DDL, OLD, new, bad)

    async def test_table_to_view_keeps_existing_table(self):
        new = {"v_records": {
            "jenis_tabel": "View", "kolom_baru": NEW["record"]["kolom_baru"],
        }}
        view_sql = "CREATE VIEW `v_records` AS SELECT `id` AS `record_id`, `name` FROM `records`;"
        runtime = FakeRuntime({"ddl_alter": view_sql, "ddl_create": view_sql})
        result = await build_ddl_standard(SOURCE_DDL, OLD, new, runtime)
        self.assertIn(view_sql, result["ddl_alter"])
        self.assertNotIn("DROP TABLE", result["ddl_alter"])

        bad = FakeRuntime({
            "ddl_alter": "RENAME TABLE `records` TO `v_records`;",
            "ddl_create": view_sql,
        })
        with self.assertRaisesRegex(DdlStandardError, "membuat View baru"):
            await build_ddl_standard(SOURCE_DDL, OLD, new, bad)

    async def test_new_view_can_be_created_alongside_existing_table(self):
        new = {
            "records": {"jenis_tabel": "Transaksi/relasi", "kolom_baru": [
                {"no_kolom": 1, "nama_kolom": "id", "log": {"no_lama": 1, "jenis_perubahan": "Dipertahankan"}},
                {"no_kolom": 2, "nama_kolom": "name", "log": {"no_lama": 2, "jenis_perubahan": "Dipertahankan"}},
            ]},
            "v_records_name": {"jenis_tabel": "View", "kolom_baru": [
                {"no_kolom": 1, "nama_kolom": "name", "log": {"no_lama": None, "jenis_perubahan": "Baru"}},
            ]},
        }
        view_sql = "CREATE VIEW `v_records_name` AS SELECT `name` FROM `records`;"

        class Runtime:
            def generate_response(self, system, prompt):
                if "instalasi baru" in system:
                    return json.dumps({"ddl_create": (
                        "CREATE TABLE `records` (`id` INT NOT NULL, `name` VARCHAR(50));\n"
                        + view_sql
                    )})
                return json.dumps({"ddl_alter": view_sql})

        result = await build_ddl_standard(SOURCE_DDL, OLD, new, Runtime())
        self.assertIn(view_sql, result["ddl_create"])
        self.assertIn(view_sql, result["ddl_alter"])

    async def test_generates_two_sql_files_from_existing_and_new(self):
        runtime = FakeRuntime({
            "ddl_alter": "ALTER TABLE `records` RENAME TO `record`;\nALTER TABLE `record` CHANGE COLUMN `id` `record_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT;",
            "ddl_create": "CREATE TABLE `record` (`record_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, `name` VARCHAR(50), PRIMARY KEY (`record_id`));",
        })
        progress = []
        result = await build_ddl_standard(SOURCE_DDL, OLD, NEW, runtime, lambda: progress.append(1))
        self.assertIn("ALTER TABLE `records`", result["ddl_alter"])
        self.assertIn("CREATE TABLE `record`", result["ddl_create"])
        self.assertNotIn("existing", runtime.calls[0]["objek"][0])
        self.assertNotIn("log", runtime.calls[0]["objek"][0]["dictionary_new"]["kolom_baru"][0])
        self.assertEqual(runtime.calls[0]["objek"][0]["dictionary_new"]["kolom_baru"][0]["nama_kolom"], "record_id")
        self.assertEqual(runtime.calls[0]["objek"][0]["referensi_ddl_lama"], {
            "nama": "records", "jenis_objek": "Table",
            "constraint": ["PRIMARY KEY (`id`)"], "opsi_tabel": "",
        })
        self.assertEqual(runtime.calls[1]["objek"][0]["existing"]["nama"], "records")
        self.assertEqual(runtime.calls[1]["objek"][0]["dictionary_new"]["kolom_baru"][0]["log"]["no_lama"], 1)
        self.assertEqual(len(runtime.calls), 2)
        self.assertEqual(progress, [1, 1])

    async def test_create_uses_existing_view_query_only_as_reference(self):
        source = b"CREATE VIEW `v_records` AS SELECT `id`, `name` FROM `records`;"
        old = {"v_records": {"kolom": {"id": {}, "name": {}}}}
        new = {"v_records": {"jenis_tabel": "View", "kolom_baru": [
            {"no_kolom": 1, "nama_kolom": "id", "log": {"no_lama": 1}},
            {"no_kolom": 2, "nama_kolom": "name", "log": {"no_lama": 2}},
        ]}}
        runtime = FakeRuntime({"ddl_create": source.decode(), "ddl_alter": source.decode()})

        await build_ddl_standard(source, old, new, runtime)

        reference = runtime.calls[0]["objek"][0]["referensi_ddl_lama"]
        self.assertEqual(reference["nama"], "v_records")
        self.assertEqual(reference["kolom"], ["id", "name"])
        self.assertIn("SELECT `id`, `name` FROM `records`", reference["query_view"])
        self.assertNotIn("dictionary_old", runtime.calls[0]["objek"][0])

    async def test_rejects_incomplete_create_columns(self):
        runtime = FakeRuntime({
            "ddl_alter": "",
            "ddl_create": "CREATE TABLE `record` (`record_id` BIGINT UNSIGNED NOT NULL);",
        })
        with self.assertRaisesRegex(DdlStandardError, "tidak sesuai urutan"):
            await build_ddl_standard(SOURCE_DDL, OLD, NEW, runtime)
        self.assertEqual(len(runtime.calls), 2)

    async def test_rejects_destructive_statement(self):
        runtime = FakeRuntime({
            "ddl_alter": "DROP TABLE `records`;",
            "ddl_create": "CREATE TABLE `record` (`record_id` BIGINT, `name` VARCHAR(50));",
        })
        with self.assertRaisesRegex(DdlStandardError, "tidak diizinkan"):
            await build_ddl_standard(SOURCE_DDL, OLD, NEW, runtime)

    async def test_allows_backfill_for_nullable_audit_timestamp(self):
        source = b"CREATE TABLE `records` (`id` int NOT NULL, `created_at` timestamp NULL DEFAULT NULL, PRIMARY KEY (`id`));"
        old = {"records": {"kolom": {"id": {}, "created_at": {}}}}
        new = {"record": {"jenis_tabel": "Transaksi/relasi", "kolom_baru": [
            {"no_kolom": 1, "nama_kolom": "record_id", "log": {"no_lama": 1, "jenis_perubahan": "Direvisi"}},
            {"no_kolom": 2, "nama_kolom": "created_at", "log": {"no_lama": 2, "jenis_perubahan": "Direvisi"}},
        ]}}
        runtime = FakeRuntime({
            "ddl_alter": (
                "UPDATE `records` SET `created_at` = CURRENT_TIMESTAMP WHERE `created_at` IS NULL;\n"
                "ALTER TABLE `records` RENAME TO `record`;\n"
                "ALTER TABLE `record` CHANGE COLUMN `id` `record_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT;\n"
                "ALTER TABLE `record` MODIFY COLUMN `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;"
            ),
            "ddl_create": "CREATE TABLE `record` (`record_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`record_id`));",
        })
        result = await build_ddl_standard(source, old, new, runtime)
        self.assertIn("UPDATE `records` SET `created_at`", result["ddl_alter"])

    async def test_rejects_update_outside_audit_timestamp_backfill(self):
        runtime = FakeRuntime({
            "ddl_alter": (
                "UPDATE `records` SET `name` = 'unknown' WHERE `name` IS NULL;\n"
                "ALTER TABLE `records` RENAME TO `record`;"
            ),
            "ddl_create": "CREATE TABLE `record` (`record_id` BIGINT, `name` VARCHAR(50));",
        })
        with self.assertRaisesRegex(DdlStandardError, "hanya mengizinkan UPDATE backfill"):
            await build_ddl_standard(SOURCE_DDL, OLD, NEW, runtime)

    async def test_rejects_incomplete_dictionary_mapping_before_llm(self):
        runtime = FakeRuntime({})
        missing = {"record": {"jenis_tabel": "Transaksi/relasi", "kolom_baru": [NEW["record"]["kolom_baru"][0]]}}
        with self.assertRaisesRegex(DdlStandardError, "tidak lengkap"):
            await build_ddl_standard(SOURCE_DDL, OLD, missing, runtime)
        self.assertEqual(runtime.calls, [])

    async def test_downloads_alter_and_create_as_sql(self):
        job = SimpleNamespace(status="completed", result={
            "ddl_alter": "ALTER TABLE `records` RENAME TO `record`;\n",
            "ddl_create": "CREATE TABLE `record` (`record_id` BIGINT);\n",
        })
        with patch.object(routes, "find_ddl_standard_job", return_value=job):
            for kind in ("alter", "create"):
                response = await routes.download_ddl_standard("job", kind)
                self.assertIn(f"ddl_{kind}.sql", response.headers["content-disposition"])
                self.assertEqual(response.body.decode(), job.result[f"ddl_{kind}"])
            with self.assertRaises(HTTPException) as error:
                await routes.download_ddl_standard("job", "other")
            self.assertEqual(error.exception.status_code, 404)
