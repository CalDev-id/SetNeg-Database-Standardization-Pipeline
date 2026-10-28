import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from api.routes import data_dictionary as dictionary_routes
from api.routes.data_dictionary import get_new_dictionary
from features.audit_db.audit import buat_batch_audit
from features.audit_db.extract import parse_schema_ddl
from features.data_dictionary import pipeline
from features.data_dictionary.dictionary_old import (
    OldDictionaryError, _validate_response as validate_old_response,
    build_old_dictionary, parse_existing_objects,
)
from features.data_dictionary.dictionary_new import (
    PROMPT_PERUBAHAN, NewDictionaryError, _batch_prompt, _generate, _parse_batch, _proposed_tables,
    build_new_dictionary, count_batches,
)
from features.data_dictionary.table_classification import (
    ClassificationError, _parse_response, classify_tables,
)


def ddl(column_counts):
    statements = []
    for index, count in enumerate(column_counts):
        columns = ", ".join(f"`field_{number}` INT" for number in range(count))
        statements.append(f"CREATE TABLE `table_{index}` ({columns});")
    return "\n".join(statements).encode()


class BatchRuntime:
    def __init__(self):
        self.calls = []

    def generate_response(self, system, user):
        data = json.loads(user.split("\nData", 1)[1].split("\n", 1)[1])
        self.calls.append(data)
        if "tabel" in data:
            return json.dumps({item["nama_tabel"]: {
                "jenis_tabel": "Master data", "deskripsi_tabel": "Tabel contoh.",
                "kolom": {name: {"comment": "Nilai contoh.", "pii": "Tidak"}
                          for name in (definition.split("`")[1] for definition in item["definisi_kolom"])}
            } for item in data["tabel"]})
        return json.dumps({item["nama_objek"]: {
            "jenis_tabel": "Master data", "deskripsi_tabel": "Tabel contoh.",
            "kolom": {name: {"comment": "Nilai contoh."}
                      for name in item["nama_kolom_berurutan"]}
        } for item in data["objek"]})


class DictionaryBatchingTests(unittest.IsolatedAsyncioTestCase):
    async def test_new_dictionary_uses_25_columns_per_table_batch(self):
        objects = parse_existing_objects(ddl([25, 45, 63]))
        self.assertEqual(count_batches(objects, []), 6)
        self.assertEqual([len(item.columns[index:index + 25])
                          for item in objects
                          for index in range(0, len(item.columns), 25)],
                         [25, 25, 20, 25, 25, 13])

        small_remainders = parse_existing_objects(ddl([26, 30, 34, 35, 51, 59, 60]))
        self.assertEqual(count_batches(small_remainders, []), 10)

    async def test_new_dictionary_preserves_column_numbers_with_merged_tail(self):
        class Runtime:
            def __init__(self):
                self.batch_sizes = []

            def generate_response(self, system, user):
                context = json.loads(user.rsplit("\n\n", 1)[-1])
                self.batch_sizes.append(len(context["kolom_ddl"]))
                return json.dumps({"table_0": {
                    "jenis_tabel": "Transaksi/relasi", "deskripsi_tabel": "Tabel contoh.",
                    "kolom_baru": [{
                        "no_kolom": index + 1, "nama_kolom": column["nama"],
                        "tipe_data": "INT", "pii": "Tidak", "_row_status": "TETAP",
                        "log": {"no_lama": column["no_lama"],
                                "jenis_perubahan": "Dipertahankan"},
                    } for index, column in enumerate(context["kolom_ddl"])],
                }})

        runtime = Runtime()
        result = await build_new_dictionary(
            ddl([59]), [], [], {"table_0": {"jenis_tabel": "Transaksi/relasi"}}, runtime,
        )
        self.assertEqual(runtime.batch_sizes, [25, 34])
        self.assertEqual([row["log"]["no_lama"] for row in result["table_0"]["kolom_baru"]],
                         list(range(1, 60)))

    async def test_normalization_can_split_table_and_record_removed_column(self):
        source = "CREATE TABLE `pegawai` (`id` INT, `jenis_pegawai` VARCHAR(50));".encode()
        finding = {
            "Nama Tabel": "pegawai", "Kolom Terdampak": "`jenis_pegawai`",
            "Solusi Normalisasi": "Pindahkan `jenis_pegawai` ke master_jenis_pegawai; tambahkan `master_jenis_pegawai_id`.",
            "Tabel Baru Usulan": "master_jenis_pegawai (id, nama)",
            "Objek Temuan": "3NF - Ketergantungan Transitif", "Tahap Normalisasi": "3NF",
        }

        def row(name, number, status, kind, position=None):
            return {
                "no_kolom": position or 1, "nama_kolom": name, "tipe_data": "INT",
                "pii": "Tidak", "_row_status": status,
                "log": {
                    "no_lama": number, "jenis_perubahan": kind,
                    "objek_temuan": "-" if kind == "Dipertahankan" else finding["Objek Temuan"],
                    "aturan_playbook": "-" if kind == "Dipertahankan" else "3NF",
                    "uraian_baru": None if number is not None else "Ditambahkan sesuai normalisasi.",
                },
            }

        response = {
            "pegawai": {
                "jenis_tabel": "Transaksi/relasi", "deskripsi_tabel": "Pegawai.",
                "kolom_dihapus": [{"no_lama": 2, "alasan": "Dipindahkan ke tabel referensi."}],
                "kolom_baru": [
                    row("id", 1, "TETAP", "Dipertahankan"),
                    row("master_jenis_pegawai_id", None, "KUNING", "Baru", 2),
                ],
            },
            "master_jenis_pegawai": {
                "jenis_tabel": "Master data", "deskripsi_tabel": "Jenis pegawai.",
                "kolom_baru": [
                    row("master_jenis_pegawai_id", None, "HIJAU", "Baru"),
                    row("nama", None, "HIJAU", "Baru", 2),
                ],
            },
        }

        class Runtime:
            def generate_response(self, system, user):
                self.system = system
                return json.dumps(response)

        runtime = Runtime()
        result = await build_new_dictionary(
            source, [], [finding], {"pegawai": {"jenis_tabel": "Transaksi/relasi"}},
            runtime,
        )
        self.assertIs(runtime.system, PROMPT_PERUBAHAN)
        self.assertEqual(set(result), {"pegawai", "master_jenis_pegawai"})
        self.assertEqual(result["pegawai"]["kolom_dihapus"][0]["no_lama"], 2)
        self.assertEqual([row["nama_kolom"] for row in result["master_jenis_pegawai"]["kolom_baru"]],
                         ["master_jenis_pegawai_id", "nama"])

        invalid = json.loads(json.dumps(response))
        invalid["pegawai"]["kolom_dihapus"] = []
        with self.assertRaisesRegex(NewDictionaryError, "tidak lengkap"):
            _parse_batch(json.dumps(invalid), parse_existing_objects(source)[0], {1, 2}, True,
                         normalization_findings=[finding], allowed_split_names={"master_jenis_pegawai"},
                         expected_columns=["id", "jenis_pegawai"])

        no_split = json.loads(json.dumps(response))
        no_split.pop("master_jenis_pegawai")
        _, _, splits = _parse_batch(json.dumps(no_split), parse_existing_objects(source)[0], {1, 2}, True,
                                    normalization_findings=[finding], allowed_split_names={"master_jenis_pegawai"},
                                    expected_columns=["id", "jenis_pegawai"])
        self.assertEqual(splits, {})

    async def test_normalization_can_propose_a_new_view(self):
        source = b"CREATE TABLE `pegawai` (`id` INT, `nama` VARCHAR(80));"
        finding = {
            "Nama Tabel": "pegawai", "Kolom Terdampak": "`nama`",
            "Solusi Normalisasi": "Sediakan view v_pegawai_fullname untuk nama lengkap.",
            "Tabel Baru Usulan": "v_pegawai_fullname (pegawai_id, fullname)",
        }

        def row(name, number, status, kind):
            return {"no_kolom": 1, "nama_kolom": name, "tipe_data": "VARCHAR(80)",
                    "pii": "Tidak", "_row_status": status,
                    "log": {"no_lama": number, "jenis_perubahan": kind}}

        response = {
            "pegawai": {"jenis_tabel": "Transaksi/relasi", "deskripsi_tabel": "Pegawai.",
                        "kolom_baru": [row("id", 1, "TETAP", "Dipertahankan"),
                                       row("nama", 2, "TETAP", "Dipertahankan")]},
            "v_pegawai_fullname": {"jenis_tabel": "View", "deskripsi_tabel": "Nama pegawai.",
                                   "kolom_baru": [row("pegawai_id", None, "HIJAU", "Baru"),
                                                  row("fullname", None, "HIJAU", "Baru")]},
        }

        class Runtime:
            def generate_response(self, system, user):
                return json.dumps(response)

        result = await build_new_dictionary(
            source, [], [finding], {"pegawai": {"jenis_tabel": "Transaksi/relasi"}}, Runtime(),
        )
        self.assertEqual(result["v_pegawai_fullname"]["jenis_tabel"], "View")
        self.assertEqual([row["nama_kolom"] for row in result["v_pegawai_fullname"]["kolom_baru"]],
                         ["pegawai_id", "fullname"])

    async def test_audit_finding_can_support_removal_and_new_column(self):
        source = b"CREATE TABLE `jabatan` (`id` INT, `nip` VARCHAR(18));"
        item = parse_existing_objects(source)[0]
        audit_finding = {
            "nama_tabel": "jabatan", "objek_temuan": "Kolom nip redundan",
            "uraian_ketidaksesuaian": "Kolom `nip` sudah ada pada tabel pegawai.",
            "solusi": "Hapus `nip` dari rancangan dan tambahkan `pegawai_id` sebagai FK.",
            "aturan_playbook": "Aturan relasi",
        }
        response = {"jabatan": {
            "jenis_tabel": "Transaksi/relasi", "deskripsi_tabel": "Jabatan pegawai.",
            "kolom_dihapus": [{"no_lama": 2, "alasan": "Kolom redundan."}],
            "kolom_baru": [
                {"no_kolom": 1, "nama_kolom": "id", "tipe_data": "INT", "pii": "Tidak",
                 "_row_status": "TETAP", "log": {"no_lama": 1, "jenis_perubahan": "Dipertahankan"}},
                {"no_kolom": 2, "nama_kolom": "pegawai_id", "tipe_data": "INT", "pii": "Tidak",
                 "_row_status": "KUNING", "log": {"no_lama": None, "jenis_perubahan": "Baru"}},
            ],
        }}
        name, table, _ = _parse_batch(
            json.dumps(response), item, {1, 2}, True, expected_columns=["id", "nip"],
            audit_findings=[audit_finding],
        )
        self.assertEqual(name, "jabatan")
        self.assertEqual(table["kolom_dihapus"][0]["no_lama"], 2)

        class Runtime:
            def generate_response(self, system, user):
                return json.dumps(response)

        result = await build_new_dictionary(
            source, [audit_finding], [], {"jabatan": {"jenis_tabel": "Transaksi/relasi"}}, Runtime(),
        )
        self.assertEqual(result["jabatan"]["kolom_dihapus"][0]["no_lama"], 2)

        unrelated = {**audit_finding, "solusi": "Ubah tipe data `nip` menjadi VARCHAR(18)."}
        _, table, _ = _parse_batch(json.dumps(response), item, {1, 2}, True,
                                   expected_columns=["id", "nip"], audit_findings=[unrelated])
        self.assertEqual(table["kolom_dihapus"][0]["no_lama"], 2)

    async def test_new_dictionary_accepts_removal_without_keyword_matching(self):
        source = b"CREATE TABLE `jabatan` (`id` INT, `nip` VARCHAR(18));"
        item = parse_existing_objects(source)[0]

        class Runtime:
            def __init__(self):
                self.calls = []

            def generate_response(self, system, user):
                self.calls.append(user)
                rows = [{"no_kolom": 1, "nama_kolom": "id", "tipe_data": "INT", "pii": "Tidak",
                         "_row_status": "TETAP", "log": {"no_lama": 1, "jenis_perubahan": "Dipertahankan"}}]
                removed = [{"no_lama": 2, "alasan": "Dianggap redundan."}]
                if len(self.calls) > 1:
                    rows.append({"no_kolom": 2, "nama_kolom": "nip", "tipe_data": "VARCHAR(18)",
                                 "pii": "Ya", "_row_status": "TETAP",
                                 "log": {"no_lama": 2, "jenis_perubahan": "Dipertahankan"}})
                    removed = []
                return json.dumps({"jabatan": {"jenis_tabel": "Transaksi/relasi",
                                               "deskripsi_tabel": "Jabatan pegawai.",
                                               "kolom_baru": rows, "kolom_dihapus": removed}})

        runtime = Runtime()
        _, table, _ = await _generate(runtime, "Data batch", item, {1, 2}, True,
                                      expected_columns=["id", "nip"])
        self.assertEqual(len(runtime.calls), 1)
        self.assertEqual(table["kolom_dihapus"][0]["no_lama"], 2)
        self.assertEqual(len(table["kolom_baru"]), 1)

    async def test_existing_master_represents_normalization_proposal(self):
        source = (
            "CREATE TABLE `jabatan` (`id` INT);\n"
            "CREATE TABLE `pegawai` (`id` INT, `jabatan_id` INT);"
        ).encode()
        finding = {
            "Nama Tabel": "pegawai", "Kolom Terdampak": "`jabatan_id`",
            "Solusi Normalisasi": "Gunakan FK ke master_jabatan.",
            "Tabel Baru Usulan": "master_jabatan (id, nama)",
        }

        class Runtime:
            def generate_response(self, system, user):
                context = json.loads(user.rsplit("\n\n", 1)[-1])
                table_name = context["nama_tabel_lama"]
                target = "master_jabatan" if table_name == "jabatan" else table_name
                rows = [{
                    "no_kolom": index + 1, "nama_kolom": column["nama"], "tipe_data": "INT",
                    "pii": "Tidak", "_row_status": "TETAP",
                    "log": {"no_lama": column["no_lama"], "jenis_perubahan": "Dipertahankan"},
                } for index, column in enumerate(context["kolom_ddl"])]
                payload = {target: {
                    "jenis_tabel": "Master data" if table_name == "jabatan" else "Transaksi/relasi",
                    "deskripsi_tabel": "Tabel.", "kolom_baru": rows,
                }}
                if table_name == "pegawai":
                    payload["master_jabatan"] = {"abaikan": "Tabel existing diproses pada batch sendiri."}
                return json.dumps(payload)

        result = await build_new_dictionary(
            source, [], [finding],
            {"jabatan": {"jenis_tabel": "Master data"},
             "pegawai": {"jenis_tabel": "Transaksi/relasi"}},
            Runtime(),
        )
        self.assertEqual(set(result), {"master_jabatan", "pegawai"})

    async def test_multiple_proposed_tables_are_read_without_splitting_column_lists(self):
        finding = {
            "Nama Tabel": "pegawai", "Kolom Terdampak": "`jenis_pegawai`",
            "Tabel Baru Usulan": "master_jenis_pegawai (id, nama), master_status_pegawai (id, nama) | -",
        }
        self.assertEqual(_proposed_tables([finding], "pegawai"),
                         {"master_jenis_pegawai", "master_status_pegawai"})
        item = parse_existing_objects(b"CREATE TABLE `pegawai` (`jenis_pegawai` INT);")[0]
        context = json.loads(_batch_prompt(item, item.columns, True, True, 1, 1, 1,
                                           {}, [], [finding], "db").rsplit("\n\n", 1)[-1])
        self.assertEqual(context["tabel_pecahan_wajib_batch_ini"],
                         ["master_jenis_pegawai", "master_status_pegawai"])

    async def test_extra_table_still_requires_valid_dictionary_structure(self):
        item = parse_existing_objects(b"CREATE TABLE `pegawai` (`id` INT);")[0]
        response = {
            "pegawai": {"jenis_tabel": "Transaksi/relasi", "deskripsi_tabel": "Pegawai.",
                        "kolom_baru": [{"no_kolom": 1, "nama_kolom": "id", "tipe_data": "INT",
                                        "pii": "Tidak", "_row_status": "TETAP",
                                        "log": {"no_lama": 1, "jenis_perubahan": "Dipertahankan"}}]},
            "master_rekaan": {"respons": "tidak lengkap"},
        }
        with self.assertRaisesRegex(NewDictionaryError, "kolom_baru"):
            _parse_batch(json.dumps(response), item, {1}, True,
                         allowed_split_names={"master_jabatan"}, expected_columns=["id"])

    async def test_valid_extra_table_does_not_need_exact_normalization_proposal(self):
        item = parse_existing_objects(b"CREATE TABLE `pegawai` (`id` INT);")[0]
        row = lambda name, number, status: {
            "no_kolom": 1, "nama_kolom": name, "tipe_data": "INT", "pii": "Tidak",
            "_row_status": status,
            "log": {"no_lama": number, "jenis_perubahan": "Baru" if number is None else "Dipertahankan"},
        }
        response = {
            "pegawai": {"jenis_tabel": "Transaksi/relasi", "deskripsi_tabel": "Pegawai.",
                        "kolom_baru": [row("id", 1, "TETAP")]},
            "master_jabatan": {"jenis_tabel": "Master data", "deskripsi_tabel": "Jabatan.",
                               "kolom_baru": [row("id", None, "HIJAU")]},
        }
        _, _, extras = _parse_batch(json.dumps(response), item, {1}, True,
                                     allowed_split_names=set(), expected_columns=["id"])
        self.assertIn("master_jabatan", extras)

    async def test_new_dictionary_receives_normalization_findings_by_table_and_batch(self):
        first, other = parse_existing_objects(ddl([36, 1]))
        first_column = {"Nama Tabel": first.name, "Kolom Terdampak": "`field_0`",
                        "Tahap Normalisasi": "3NF", "Tabel Baru Usulan": "master_jabatan"}
        last_column = {"Nama Tabel": first.name, "Kolom Terdampak": "`field_25`",
                       "Tahap Normalisasi": "2NF", "Tabel Baru Usulan": "-"}
        other_table = {"Nama Tabel": other.name, "Kolom Terdampak": "`field_0`",
                       "Tahap Normalisasi": "1NF", "Tabel Baru Usulan": "-"}
        findings = [first_column, last_column, other_table]

        def context(item, columns, first_batch):
            prompt = _batch_prompt(
                item, columns, first_batch, not first_batch, 1, 1 if first_batch else 2,
                2, {}, [], findings, "db",
            )
            return json.loads(prompt.rsplit("\n\n", 1)[-1])

        first_context = context(first, first.columns[:25], True)
        last_context = context(first, first.columns[25:], False)
        other_context = context(other, other.columns, True)
        self.assertEqual(first_context["temuan_normalisasi"], [first_column, last_column])
        self.assertEqual(last_context["temuan_normalisasi"], [last_column])
        self.assertEqual(other_context["temuan_normalisasi"], [other_table])
        self.assertEqual(first_context["temuan_tabel"], [])

    async def test_classification_always_uses_telkom_runtime(self):
        source = ddl([1])
        runtime = object()
        with patch.object(pipeline, "get_runtime", return_value=runtime) as get_runtime, \
             patch.object(pipeline, "_run_job", new_callable=AsyncMock) as run_job, \
             patch.dict(pipeline._jobs, clear=True):
            await pipeline.start_classification_job(source, [], asyncio.Semaphore(1), "audit")
            await asyncio.sleep(0)
        get_runtime.assert_called_once_with("telkom")
        self.assertIs(run_job.await_args.args[3], runtime)

    async def test_small_tables_share_requests_and_keep_all_columns(self):
        source = ddl([10] * 6)
        parsed = parse_schema_ddl(source)
        audit_batches = buat_batch_audit(parsed, 50, 5)
        self.assertEqual([len(batch) for batch in audit_batches], [5, 1])

        classification_runtime = BatchRuntime()
        classification = await classify_tables(parsed, [], classification_runtime)
        self.assertEqual([len(call["tabel"]) for call in classification_runtime.calls], [5, 1])
        self.assertEqual(len(classification), 6)
        self.assertTrue(all(len(table["kolom"]) == 10 for table in classification.values()))

        old_runtime = BatchRuntime()
        old = await build_old_dictionary(source, old_runtime)
        self.assertEqual([len(call["objek"]) for call in old_runtime.calls], [3, 3])
        self.assertEqual(len(old), 6)
        self.assertTrue(all(len(table["kolom"]) == 10 for table in old.values()))

    async def test_small_remainder_is_combined_up_to_ten_columns(self):
        audit_60 = buat_batch_audit(parse_schema_ddl(ddl([50, 10])), 50, 5)
        audit_61 = buat_batch_audit(parse_schema_ddl(ddl([50, 11])), 50, 5)
        self.assertEqual([[len(part.columns) for part in batch] for batch in audit_60], [[50, 10]])
        self.assertEqual([[len(part.columns) for part in batch] for batch in audit_61], [[50], [11]])
        self.assertEqual([len(batch[0].columns) for batch in
                          buat_batch_audit(parse_schema_ddl(ddl([60])), 50, 5)], [60])
        self.assertEqual([len(batch[0].columns) for batch in
                          buat_batch_audit(parse_schema_ddl(ddl([61])), 50, 5)], [50, 11])

        classification_runtime = BatchRuntime()
        await classify_tables(parse_schema_ddl(ddl([50, 10])), [], classification_runtime)
        self.assertEqual([len(call["tabel"]) for call in classification_runtime.calls], [2])

        old_runtime = BatchRuntime()
        await build_old_dictionary(ddl([30, 10]), old_runtime)
        self.assertEqual([len(call["objek"]) for call in old_runtime.calls], [2])

    async def test_column_limit_keeps_tables_whole(self):
        source = ddl([30, 21])
        parsed = parse_schema_ddl(source)
        runtime = BatchRuntime()
        await classify_tables(parsed, [], runtime)
        self.assertEqual([len(call["tabel"]) for call in runtime.calls], [2])

        old_runtime = BatchRuntime()
        await build_old_dictionary(source, old_runtime)
        self.assertEqual([len(call["objek"]) for call in old_runtime.calls], [1, 1])
        self.assertEqual([len(item.columns) for item in parse_existing_objects(source)], [30, 21])

    async def test_classification_ignores_other_ddl_tables_but_requires_batch_target(self):
        parsed = parse_schema_ddl(ddl([30, 31]))

        class ExtraTableRuntime(BatchRuntime):
            def generate_response(self, system, user):
                result = json.loads(super().generate_response(system, user))
                other = next(name for name in self.calls[-1]["semua_nama_tabel"] if name not in result)
                result[other] = {"bukan_target_batch": True}
                return json.dumps(result)

        runtime = ExtraTableRuntime()
        classification = await classify_tables(parsed, [], runtime)
        self.assertEqual(set(classification), {"table_0", "table_1"})
        self.assertEqual(len(runtime.calls), 2)
        self.assertEqual(len(classification["table_0"]["kolom"]), 30)
        self.assertEqual(len(classification["table_1"]["kolom"]), 31)

        expected = {"jabatan": {"id"}}
        valid = {"jenis_tabel": "Master data", "deskripsi_tabel": "Jabatan.",
                 "kolom": {"id": {"comment": "ID.", "pii": "Tidak"}}}
        self.assertEqual(_parse_response(json.dumps({"jabatan": valid, "fiktif": {}}), expected,
                                         {"jabatan", "pegawai"})["jabatan"]["kolom"].keys(), {"id"})
        fallback = _parse_response(json.dumps({"pegawai": {}}), expected, {"jabatan", "pegawai"})
        self.assertEqual(set(fallback["jabatan"]["kolom"]), {"id"})

    async def test_classification_and_old_dictionary_ignore_extra_columns(self):
        source = b"CREATE TABLE `jabatan` (`id` INT);"
        classified = {"jabatan": {"jenis_tabel": "Master data", "deskripsi_tabel": "Jabatan.",
                                  "kolom": {"id": {"comment": "ID.", "pii": "Tidak"},
                                            "rekaan": {"bukan_format": True}}}}
        result = _parse_response(json.dumps(classified), {"jabatan": {"id"}})
        self.assertEqual(set(result["jabatan"]["kolom"]), {"id"})

        old = {"jabatan": {"jenis_tabel": "Master data", "deskripsi_tabel": "Jabatan.",
                           "kolom": {"id": {"comment": "ID."}, "rekaan": {"bukan_format": True}}},
               "tabel_lain": {"bukan_format": True}}
        items = parse_existing_objects(source)
        self.assertEqual(set(validate_old_response(json.dumps(old), items)["jabatan"]["kolom"]), {"id"})
        del old["jabatan"]["kolom"]["id"]
        self.assertEqual(validate_old_response(json.dumps(old), items)["jabatan"]["kolom"]["id"]["comment"],
                         "Deskripsi belum tersedia; perlu ditinjau.")

    async def test_single_large_table_fills_missing_column_classification(self):
        source = ddl([3])
        parsed = parse_schema_ddl(source)

        class RepairRuntime:
            def __init__(self):
                self.prompts = []

            def generate_response(self, system, user):
                self.prompts.append(user)
                columns = ["field_0", "field_1", "field_2"]
                if len(self.prompts) == 1:
                    columns.remove("field_2")
                if len(self.prompts) == 2:
                    columns.remove("field_1")
                return json.dumps({"table_0": {
                    "jenis_tabel": "Master data", "deskripsi_tabel": "Tabel contoh.",
                    "kolom": {name: {"comment": "Nilai contoh.", "pii": "Tidak"}
                              for name in columns},
                }})

        runtime = RepairRuntime()
        classification = await classify_tables(parsed, [], runtime)
        self.assertEqual(len(runtime.prompts), 1)
        self.assertEqual(set(classification["table_0"]["kolom"]), {"field_0", "field_1", "field_2"})

    async def test_new_dictionary_retries_when_table_name_changes(self):
        item = parse_existing_objects(ddl([1]))[0]

        class RenameRuntime:
            def __init__(self):
                self.calls = 0

            def generate_response(self, system, user):
                assert system == PROMPT_PERUBAHAN
                self.calls += 1
                name = item.name if self.calls == 1 else "master_table_0"
                return json.dumps({name: {
                    "jenis_tabel": "Master data", "deskripsi_tabel": "Tabel contoh.",
                    "kolom_baru": [{
                        "no_kolom": 1, "nama_kolom": "field_0", "tipe_data": "INT",
                        "pii": "Tidak", "_row_status": "TETAP",
                        "log": {"no_lama": 1, "jenis_perubahan": "Dipertahankan"},
                    }],
                }})

        runtime = RenameRuntime()
        name, _, _ = await _generate(runtime, "Batch 2", item, {1}, False, "master_table_0")
        self.assertEqual(name, "master_table_0")
        self.assertEqual(runtime.calls, 2)

    async def test_new_dictionary_repairs_duplicate_name_across_batches(self):
        source = ddl([36])

        class DuplicateRuntime:
            def __init__(self):
                self.calls = []

            def generate_response(self, system, user):
                context = json.loads(user.split("\n\n", 1)[1].split("\n\nRespons sebelumnya", 1)[0])
                self.calls.append(user)
                duplicate = context["batch"] == 2 and len(self.calls) == 2
                rows = [{
                    "no_kolom": index + 1,
                    "nama_kolom": "field_1" if duplicate else column["nama"],
                    "tipe_data": "INT", "pii": "Tidak", "_row_status": "TETAP",
                    "log": {"no_lama": column["no_lama"], "jenis_perubahan": "Dipertahankan"},
                } for index, column in enumerate(context["kolom_ddl"])]
                return json.dumps({"table_0": {
                    "jenis_tabel": "Transaksi/relasi", "deskripsi_tabel": "Tabel contoh.",
                    "kolom_baru": rows,
                }})

        runtime = DuplicateRuntime()
        progress = []
        result = await build_new_dictionary(
            source, [], [], {"table_0": {"jenis_tabel": "Transaksi/relasi"}},
            runtime, lambda: progress.append(1),
        )
        self.assertEqual(len(runtime.calls), 3)
        self.assertIn("field_1", runtime.calls[2])
        self.assertEqual(len(progress), 2)
        self.assertEqual(len({row["nama_kolom"] for row in result["table_0"]["kolom_baru"]}), 36)

    async def test_failed_batch_retry_reuses_valid_checkpoint(self):
        source = ddl([36])
        classification = {"table_0": {"jenis_tabel": "Transaksi/relasi"}}
        checkpoint = {}

        class Runtime:
            def __init__(self, duplicate):
                self.duplicate = duplicate
                self.batches = []

            def generate_response(self, system, user):
                context = json.loads(user.split("\n\n", 1)[1].split("\n\nRespons sebelumnya", 1)[0])
                self.batches.append(context["batch"])
                rows = [{
                    "no_kolom": index + 1,
                    "nama_kolom": "field_1" if self.duplicate and context["batch"] == 2 else column["nama"],
                    "tipe_data": "INT", "pii": "Tidak", "_row_status": "TETAP",
                    "log": {"no_lama": column["no_lama"], "jenis_perubahan": "Dipertahankan"},
                } for index, column in enumerate(context["kolom_ddl"])]
                return json.dumps({"table_0": {
                    "jenis_tabel": "Transaksi/relasi", "deskripsi_tabel": "Tabel contoh.",
                    "kolom_baru": rows,
                }})

        invalid_runtime = Runtime(True)
        with self.assertRaisesRegex(NewDictionaryError, "field_1"):
            await build_new_dictionary(source, [], [], classification, invalid_runtime,
                                       checkpoint=checkpoint)
        self.assertEqual(invalid_runtime.batches, [1, 2, 2, 2])
        self.assertEqual(set(checkpoint), {("table_0", 0)})

        valid_runtime = Runtime(False)
        result = await build_new_dictionary(source, [], [], classification, valid_runtime,
                                            checkpoint=checkpoint)
        self.assertEqual(valid_runtime.batches, [2])
        self.assertEqual(len(result["table_0"]["kolom_baru"]), 36)

        invalid_runtime.model = valid_runtime.model = "same-model"
        with patch.object(pipeline, "get_runtime", side_effect=[invalid_runtime, valid_runtime, valid_runtime]), \
             patch.object(pipeline.logger, "warning") as warning, \
             patch.dict(pipeline._new_jobs, clear=True):
            first_id = await pipeline.start_new_dictionary_job(
                source, [], [], classification, "gpt_setneg", asyncio.Semaphore(1), "audit-1",
            )
            await asyncio.gather(*list(pipeline._tasks))
            first_job = pipeline.find_new_dictionary_job(first_id)
            self.assertEqual(first_job.status, "failed")
            self.assertEqual(first_job.error, "Dictionary New gagal. Coba lagi.")
            self.assertEqual(first_job.error_reason, "Struktur respons LLM tidak sesuai.")
            self.assertIn("field_1", str(warning.call_args.args[2]))
            self.assertEqual(len(first_job.checkpoint), 1)
            self.assertEqual((await get_new_dictionary(first_id))["saved_batches"], 1)
            self.assertEqual((await get_new_dictionary(first_id))["error"], "Dictionary New gagal. Coba lagi.")
            self.assertEqual((await get_new_dictionary(first_id))["error_reason"], first_job.error_reason)
            pipeline._new_jobs["later-failure"] = pipeline.NewDictionaryJob(
                status="failed", completed_batches=0, total_batches=2,
                started_at=first_job.started_at, audit_job_id="audit-1",
                input_key=first_job.input_key, finished_at=first_job.finished_at,
            )

            with self.assertRaisesRegex(ValueError, "Input atau model berubah"):
                await pipeline.start_new_dictionary_job(
                    source, [], [], classification, "gemini", asyncio.Semaphore(1), "audit-1",
                    retry_job_id=first_id,
                )

            second_id = await pipeline.start_new_dictionary_job(
                source, [], [], classification, "gpt_setneg", asyncio.Semaphore(1), "audit-1",
                retry_job_id=first_id,
            )
            queued = await get_new_dictionary(second_id)
            self.assertEqual(queued["completed_batches"], 1)
            self.assertEqual(queued["total_batches"], 2)
            await asyncio.gather(*list(pipeline._tasks))
            second = pipeline.find_new_dictionary_job(second_id)
            self.assertEqual(second.status, "completed")
            self.assertEqual(second.completed_batches, 2)
            self.assertEqual((await get_new_dictionary(second_id))["saved_batches"], 0)
            self.assertEqual(valid_runtime.batches, [2, 2])

    async def test_retry_uses_saved_inputs_when_audit_has_expired(self):
        source = ddl([1])
        previous = pipeline.NewDictionaryJob(
            "failed", 49, 62, 0, "audit-1", "input-key",
            source_ddl=source, findings=[], normalization_findings=[],
            classification={"table_0": {"jenis_tabel": "Transaksi/relasi"}},
            model="gpt_setneg",
        )
        data = dictionary_routes.NewDictionaryRequest(
            audit_job_id="audit-1", normalization_job_id="expired-normalization",
            classification_job_id="expired-classification", model="gpt_setneg",
            retry_job_id="failed-job",
        )
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
            audit_semaphore=asyncio.Semaphore(1))))
        with patch.object(dictionary_routes, "find_new_dictionary_job", return_value=previous), \
             patch.object(dictionary_routes, "find_spreadsheet_job") as find_audit, \
             patch.object(dictionary_routes, "find_classification_job") as find_classification, \
             patch.object(dictionary_routes, "require_completed_normalization") as require_normalization, \
             patch.object(dictionary_routes, "start_new_dictionary_job", new_callable=AsyncMock,
                          return_value="continued-job") as start:
            response = await dictionary_routes.create_new_dictionary(data, request)
        self.assertEqual(response["job_id"], "continued-job")
        self.assertEqual(start.await_args.args[:4],
                         (source, [], [], previous.classification))
        self.assertEqual(start.await_args.args[-1], "failed-job")
        find_audit.assert_not_called()
        find_classification.assert_not_called()
        require_normalization.assert_not_called()

    async def test_telkom_dictionary_new_uses_longer_timeout_with_two_attempts(self):
        runtime = type(
            "Runtime",
            (),
            {"max_attempts": 5, "read_timeout_seconds": 120, "model": "same-model"},
        )()
        with patch.object(pipeline, "get_runtime", return_value=runtime), \
             patch.object(pipeline, "build_new_dictionary", new_callable=AsyncMock, return_value={}), \
             patch.dict(pipeline._new_jobs, clear=True):
            await pipeline.start_new_dictionary_job(
                ddl([1]), [], [], {"table_0": {"jenis_tabel": "Transaksi/relasi"}},
                "telkom", asyncio.Semaphore(1), "audit-1",
            )
            await asyncio.gather(*list(pipeline._tasks))
        self.assertEqual(runtime.max_attempts, 2)
        self.assertEqual(runtime.read_timeout_seconds, 180)

    async def test_telkom_dictionary_light_task_keeps_short_timeout(self):
        runtime = type("Runtime", (), {"max_attempts": 5, "read_timeout_seconds": 120})()
        with patch.object(pipeline, "get_runtime", return_value=runtime):
            self.assertIs(pipeline.get_dictionary_runtime("telkom"), runtime)
        self.assertEqual(runtime.max_attempts, 2)
        self.assertEqual(runtime.read_timeout_seconds, 90)

    async def test_telkom_log_perubahan_uses_longer_timeout(self):
        runtime = type("Runtime", (), {"max_attempts": 5, "read_timeout_seconds": 120})()
        with patch.object(pipeline, "get_runtime", return_value=runtime), \
             patch.object(pipeline, "build_log_perubahan", new_callable=AsyncMock, return_value={}), \
             patch.dict(pipeline._log_jobs, clear=True):
            await pipeline.start_log_perubahan_job({}, {}, [], "telkom", asyncio.Semaphore(1))
            await asyncio.gather(*list(pipeline._tasks))
        self.assertEqual(runtime.max_attempts, 2)
        self.assertEqual(runtime.read_timeout_seconds, 180)

    async def test_new_metadata_table_keeps_green_status(self):
        class Runtime:
            def generate_response(self, _system, user):
                if user.startswith("Buat hanya tabel baru `metadata_database`"):
                    names = (["metadata_database_id"]
                             + [f"metadata_field_{number}" for number in range(1, 12)]
                             + ["spbe_metadata_database_id", "created_at", "updated_at",
                                "created_by", "updated_by", "deleted_at", "is_deleted"])
                    rows = [{
                        "no_kolom": number, "nama_kolom": name, "tipe_data": "VARCHAR(100)",
                        "_row_status": "HIJAU", "log": {"no_lama": None, "jenis_perubahan": "Baru"},
                    } for number, name in enumerate(names, 1)]
                    return json.dumps({"metadata_database": {
                        "jenis_tabel": "Master data", "kolom_baru": rows,
                    }})
                return json.dumps({"table_0": {
                    "jenis_tabel": "Transaksi/relasi",
                    "kolom_baru": [{
                        "nama_kolom": "field_0", "tipe_data": "INT",
                        "log": {"no_lama": 1, "jenis_perubahan": "Dipertahankan"},
                    }],
                }})

        result = await build_new_dictionary(
            ddl([1]), [{"objek_temuan": "Tabel metadata database"}], [],
            {"table_0": {"jenis_tabel": "Transaksi/relasi"}}, Runtime(),
        )
        metadata = result["metadata_database"]["kolom_baru"]
        self.assertEqual(len(metadata), 19)
        self.assertTrue(all(row["_row_status"] == "HIJAU" for row in metadata))
