import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from api.routes import ddl_standard as routes
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
    async def test_generates_two_sql_files_from_existing_and_new(self):
        runtime = FakeRuntime({
            "ddl_alter": "ALTER TABLE `records` RENAME TO `record`;\nALTER TABLE `record` CHANGE COLUMN `id` `record_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT;",
            "ddl_create": "CREATE TABLE `record` (`record_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, `name` VARCHAR(50), PRIMARY KEY (`record_id`));",
        })
        progress = []
        result = await build_ddl_standard(SOURCE_DDL, OLD, NEW, runtime, lambda: progress.append(1))
        self.assertIn("ALTER TABLE `records`", result["ddl_alter"])
        self.assertIn("CREATE TABLE `record`", result["ddl_create"])
        self.assertEqual(runtime.calls[0]["existing"]["nama"], "records")
        self.assertEqual(progress, [1])

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
