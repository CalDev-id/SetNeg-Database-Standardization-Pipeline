"""Regression tests for incomplete and empty LLM responses."""

import asyncio
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import requests

from api.routes import audit_db as audit_routes
from features.audit_db import pipeline as audit_pipeline
from features.audit_db.audit import AuditError, FormatTemuanError, audit_ddl, baca_respons_temuan
from features.audit_db.extract import parse_schema_ddl
from shared.llm.openai_runtime import NutaralineRuntime, OpenAIRuntime, OpenAIRuntimeError
from shared.llm.runtime import get_runtime
from shared.llm.telkom_gpt_runtime import GPTRunTime, TelkomRuntimeError


class FakeResponse:
    headers = {}

    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


class LlmFailureTests(unittest.TestCase):
    def test_nutaraline_uses_own_key_model_and_max_tokens(self):
        with patch.dict(os.environ, {"NUTARALINE_API_KEY": "test-nutaraline-key"}):
            runtime = get_runtime("nutaraline")
        self.assertIsInstance(runtime, NutaralineRuntime)
        with patch("shared.llm.openai_runtime.requests.post", return_value=FakeResponse("[]")) as post:
            self.assertEqual(runtime.generate_response("system", "user"), "[]")
        args = post.call_args
        self.assertEqual(args.args[0], "https://nutaraline.co.uk/v1/chat/completions")
        self.assertEqual(args.kwargs["headers"]["Authorization"], "Bearer test-nutaraline-key")
        self.assertEqual(args.kwargs["json"]["model"], "deepseek-v4.1-flash-1017")
        self.assertEqual(args.kwargs["json"]["max_tokens"], 30000)
        self.assertNotIn("max_completion_tokens", args.kwargs["json"])
        self.assertNotIn("reasoning_effort", args.kwargs["json"])
        self.assertEqual(args.kwargs["timeout"], (10, 300))

    def test_nutaraline_does_not_repeat_ambiguous_network_failure(self):
        with patch.dict(os.environ, {"NUTARALINE_API_KEY": "test-nutaraline-key"}):
            runtime = NutaralineRuntime()
        with patch("shared.llm.openai_runtime.requests.post",
                   side_effect=requests.ReadTimeout()) as post:
            with self.assertRaisesRegex(OpenAIRuntimeError, "Nutaraline melewati batas waktu"):
                runtime.generate_response("system", "user")
        post.assert_called_once()

    def test_audit_rejects_truncated_array_instead_of_accepting_partial_findings(self):
        finding = {
            "No": 1,
            "Nama Database": "db",
            "Nama Tabel": "pegawai",
            "Objek Temuan": "kolom",
            "Aturan Playbook/UU": "aturan",
            "Uraian Ketidaksesuaian": "uraian",
            "Solusi": "solusi",
            "Status": "To Do",
            "Catatan": "-",
        }
        incomplete = "[" + json.dumps(finding) + ', {"No": 2'
        with self.assertRaisesRegex(FormatTemuanError, "terpotong"):
            baca_respons_temuan(incomplete, ["pegawai"], "db", False)

    def test_gpt_setneg_retries_empty_response(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            runtime = OpenAIRuntime()
        runtime.max_attempts = 2
        with patch("shared.llm.openai_runtime.requests.post", side_effect=[
            FakeResponse(""), FakeResponse("[]"),
        ]) as post, patch("shared.llm.openai_runtime.time.sleep"):
            self.assertEqual(runtime.generate_response("system", "user"), "[]")
        self.assertEqual(post.call_count, 2)

    def test_one_call_runtime_still_fails_on_empty_response(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            runtime = OpenAIRuntime()
        runtime.max_attempts = 1
        with patch("shared.llm.openai_runtime.requests.post", return_value=FakeResponse("")) as post:
            with self.assertRaisesRegex(OpenAIRuntimeError, "respons kosong"):
                runtime.generate_response("system", "user")
        self.assertEqual(post.call_count, 1)

    def test_empty_response_logs_provider_finish_reason_and_token_usage(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            runtime = OpenAIRuntime()
        runtime.max_attempts = 2
        response = FakeResponse("")
        response.json = lambda: {
            "choices": [{"message": {"content": None}, "finish_reason": "length"}],
            "usage": {"completion_tokens": 15000,
                      "completion_tokens_details": {"reasoning_tokens": 15000}},
        }
        with patch("shared.llm.openai_runtime.requests.post", return_value=response) as post, \
             patch("shared.llm.openai_runtime.logger.warning") as warning:
            with self.assertRaisesRegex(OpenAIRuntimeError, "batas token respons"):
                runtime.generate_response("system", "user")
        post.assert_called_once()
        self.assertEqual(warning.call_args.args[2:], ("length", 15000, 15000))

    def test_gpt_setneg_retries_provider_http_524(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            runtime = OpenAIRuntime()
        runtime.max_attempts = 2
        with patch("shared.llm.openai_runtime.requests.post", side_effect=[
            FakeResponse("", 524), FakeResponse("[]"),
        ]) as post, patch("shared.llm.openai_runtime.time.sleep"):
            self.assertEqual(runtime.generate_response("system", "user"), "[]")
        self.assertEqual(post.call_count, 2)

    def test_gpt_setneg_logs_usage_without_prompt_or_response(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            runtime = OpenAIRuntime()
        response = FakeResponse("[]")
        response.json = lambda: {
            "choices": [{"message": {"content": "[]"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20,
                      "prompt_tokens_details": {"cached_tokens": 80}},
        }
        with patch("shared.llm.openai_runtime.requests.post", return_value=response), \
             patch("shared.llm.openai_runtime.logger.info") as log:
            self.assertEqual(runtime.generate_response("system", "user"), "[]")
        log.assert_called_once_with(
            "GPT Setneg usage model=%s input=%s cached=%s output=%s",
            runtime.model, 100, 80, 20,
        )

    def test_audit_gpt_setneg_timeout_does_not_repeat_same_request_five_times(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            runtime = OpenAIRuntime()
        with patch.object(audit_routes, "get_runtime", return_value=runtime):
            self.assertIs(audit_routes.get_audit_runtime("gpt_setneg"), runtime)
        self.assertEqual(runtime.max_attempts, 1)
        self.assertEqual(runtime.timeout_seconds, (10, 300))
        with patch("shared.llm.openai_runtime.requests.post",
                   side_effect=requests.ReadTimeout("timed out")) as post, \
             patch("shared.llm.openai_runtime.time.sleep") as sleep:
            with self.assertRaisesRegex(OpenAIRuntimeError, "melewati batas waktu respons") as failure:
                runtime.generate_response("system", "user")
        self.assertIn("ReadTimeout", str(failure.exception))
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs["timeout"], (10, 300))
        sleep.assert_not_called()

    def test_telkom_connection_failure_has_bounded_connect_timeout_and_cause(self):
        with patch.dict(os.environ, {"TELKOM_GPT_API_KEY": "test-key"}):
            runtime = GPTRunTime()
        runtime.max_attempts = 2
        with patch("shared.llm.telkom_gpt_runtime.requests.post",
                   side_effect=requests.ConnectTimeout("connection timed out")) as post, \
             patch("shared.llm.telkom_gpt_runtime.time.sleep"):
            with self.assertRaisesRegex(TelkomRuntimeError, "ConnectTimeout"):
                runtime.generate_response("system", "user")
        self.assertEqual(post.call_count, 2)
        self.assertEqual(post.call_args.kwargs["timeout"], (10, 120))


class AuditRetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_token_limit_retry_expands_budget_only_for_failed_batch(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "gpt-6-luna"}):
            runtime = OpenAIRuntime()
        runtime.max_attempts = 1
        initial_limit = runtime.max_completion_tokens

        def length_response(tokens):
            response = FakeResponse("")
            response.json = lambda: {
                "choices": [{"message": {"content": None}, "finish_reason": "length"}],
                "usage": {"completion_tokens": tokens},
            }
            return response

        source = b"CREATE TABLE `pegawai` (`id` INT);"
        semaphore = asyncio.Semaphore(1)
        with patch.dict(audit_pipeline._jobs, clear=True), \
             patch("shared.llm.openai_runtime.requests.post",
                   side_effect=[length_response(initial_limit), length_response(30000),
                                FakeResponse("[]")]) as post:
            job_id = await audit_pipeline.start_spreadsheet_job(source, "schema.sql", semaphore, runtime)
            await asyncio.gather(*list(audit_pipeline._tasks))
            job = audit_pipeline.find_spreadsheet_job(job_id)
            self.assertEqual(job.status, "failed")
            self.assertTrue(job.output_limit_hit)
            self.assertEqual(post.call_args_list[0].kwargs["json"]["max_completion_tokens"], initial_limit)
            self.assertNotIn("reasoning_effort", post.call_args_list[0].kwargs["json"])

            audit_pipeline.retry_spreadsheet_job(job_id, semaphore)
            await asyncio.gather(*list(audit_pipeline._tasks))
            self.assertEqual(job.status, "failed")
            self.assertEqual(post.call_args_list[1].kwargs["json"]["max_completion_tokens"], 30000)
            self.assertEqual(post.call_args_list[1].kwargs["json"]["reasoning_effort"], "low")

            audit_pipeline.retry_spreadsheet_job(job_id, semaphore)
            await asyncio.gather(*list(audit_pipeline._tasks))
            self.assertEqual(job.status, "completed")
            self.assertEqual(post.call_count, 3)
            self.assertEqual(post.call_args_list[2].kwargs["json"]["max_completion_tokens"], 45000)
            self.assertEqual(post.call_args_list[2].kwargs["json"]["reasoning_effort"], "none")
            self.assertTrue(any("batas token ditambah" in event["message"]
                                for event in job.process_events))

    async def test_failed_audit_resumes_from_failed_batch_with_previous_findings(self):
        class Runtime:
            def __init__(self):
                self.calls = []

            def generate_response(self, _system, user):
                batch, _ = json.JSONDecoder().raw_decode(user.split("Data batch:\n", 1)[1])
                table = batch["tabel"][0]["nama_tabel"]
                self.calls.append(table)
                if table == "b" and self.calls.count("b") == 1:
                    raise OpenAIRuntimeError("GPT Setneg mengembalikan HTTP 502.")
                if table == "a":
                    return json.dumps([{
                        "No": 1, "Nama Database": "-", "Nama Tabel": "a",
                        "Objek Temuan": "kolom", "Aturan Playbook/UU": "aturan",
                        "Uraian Ketidaksesuaian": "uraian", "Solusi": "solusi",
                        "Status": "To Do", "Catatan": "-",
                    }])
                return "[]"

        source = (
            "CREATE TABLE `a` (" + ", ".join(f"`a_{index}` INT" for index in range(50)) + ");\n"
            "CREATE TABLE `b` (" + ", ".join(f"`b_{index}` INT" for index in range(50)) + ");"
        ).encode()
        runtime = Runtime()
        semaphore = asyncio.Semaphore(1)
        with patch.dict(audit_pipeline._jobs, clear=True):
            job_id = await audit_pipeline.start_spreadsheet_job(source, "schema.sql", semaphore, runtime)
            await asyncio.gather(*list(audit_pipeline._tasks))
            job = audit_pipeline.find_spreadsheet_job(job_id)
            self.assertEqual(job.status, "failed")
            self.assertEqual((job.completed_batches, job.total_batches), (1, 2))
            self.assertEqual(len(job.partial_findings), 1)
            self.assertEqual(runtime.calls, ["a", "b"])

            with self.assertRaisesRegex(LookupError, "tidak ditemukan"):
                audit_pipeline.retry_spreadsheet_job("other", semaphore)

            request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(audit_semaphore=semaphore)))
            response = await audit_routes.retry_audit_spreadsheet_job(job_id, request)
            self.assertEqual(response["completed_batches"], 1)
            with self.assertRaisesRegex(ValueError, "Hanya pekerjaan"):
                audit_pipeline.retry_spreadsheet_job(job_id, semaphore)
            await asyncio.gather(*list(audit_pipeline._tasks))
            self.assertEqual(job.status, "completed")
            self.assertEqual(job.completed_batches, 2)
            self.assertEqual(runtime.calls, ["a", "b", "b"])
            self.assertEqual([item["nama_tabel"] for item in job.audit_result["findings"]], ["a"])
            self.assertTrue(any(event["kind"] == "retry" and "batch 2/2" in event["message"]
                                for event in job.process_events))

    async def test_empty_gpt_setneg_response_retries_same_batch_once(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            runtime = OpenAIRuntime()
        runtime.max_attempts = 1
        events = []
        parsed = parse_schema_ddl(b"CREATE TABLE `a` (`id` INT);\nCREATE TABLE `b` (`id` INT);")
        with patch("shared.llm.openai_runtime.requests.post", side_effect=[
            FakeResponse(""), FakeResponse("[]"),
        ]) as post:
            self.assertEqual(await audit_ddl(
                parsed, runtime, on_event=lambda kind, message: events.append((kind, message)),
            ), [])
        self.assertEqual(post.call_count, 2)
        self.assertTrue(any(kind == "retry" and "batch 1/1" in message
                            and "respons kosong" in message for kind, message in events))
        self.assertFalse(any("dipecah" in message for _, message in events))

    async def test_two_empty_gpt_setneg_responses_fail_with_batch_log(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            runtime = OpenAIRuntime()
        runtime.max_attempts = 1
        events = []
        parsed = parse_schema_ddl(b"CREATE TABLE `a` (`id` INT);\nCREATE TABLE `b` (`id` INT);")
        with patch("shared.llm.openai_runtime.requests.post", return_value=FakeResponse("")) as post:
            with self.assertRaises(AuditError):
                await audit_ddl(parsed, runtime,
                                on_event=lambda kind, message: events.append((kind, message)))
        self.assertEqual(post.call_count, 2)
        self.assertTrue(any(kind == "failed" and "batch 1/1" in message
                            and "respons kosong" in message for kind, message in events))
        self.assertFalse(any("dipecah" in message for _, message in events))

    async def test_token_limit_empty_response_fails_without_repeating_paid_request(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            runtime = OpenAIRuntime()
        runtime.max_attempts = 1
        response = FakeResponse("")
        response.json = lambda: {
            "choices": [{"message": {"content": None}, "finish_reason": "length"}],
            "usage": {"completion_tokens": 15000},
        }
        events = []
        parsed = parse_schema_ddl(b"CREATE TABLE `pegawai` (`id` INT);")
        with patch("shared.llm.openai_runtime.requests.post", return_value=response) as post:
            with self.assertRaises(AuditError):
                await audit_ddl(parsed, runtime,
                                on_event=lambda kind, message: events.append((kind, message)))
        post.assert_called_once()
        self.assertTrue(any(kind == "failed" and "batas token respons" in message
                            for kind, message in events))
        self.assertFalse(any(kind == "retry" for kind, _ in events))

    async def test_invalid_audit_response_fails_without_splitting_batch(self):
        class Runtime:
            def __init__(self):
                self.calls = 0

            def generate_response(self, _system, _user):
                self.calls += 1
                return "not JSON"

        runtime = Runtime()
        events = []
        parsed = parse_schema_ddl(b"CREATE TABLE `a` (`id` INT);\nCREATE TABLE `b` (`id` INT);")
        with patch("features.audit_db.audit.perbaiki_respons_json", new_callable=AsyncMock,
                   return_value=None):
            with self.assertRaises(AuditError):
                await audit_ddl(
                    parsed, runtime, on_event=lambda kind, message: events.append((kind, message)),
                )
        self.assertEqual(runtime.calls, 2)
        self.assertTrue(any(kind == "failed" and "batch 1/1" in message
                            for kind, message in events))
        self.assertFalse(any("dipecah" in message for _, message in events))

    async def test_gpt_setneg_read_timeout_fails_without_splitting_batch(self):
        class Runtime:
            batch_size = 50

            def __init__(self):
                self.calls = []

            def generate_response(self, _system, user):
                names = [table["nama_tabel"] for table in json.loads(
                    user.split("Data batch:\n", 1)[1]
                )["tabel"]]
                self.calls.append(names)
                timeout = requests.ReadTimeout("timed out")
                raise OpenAIRuntimeError("Koneksi ke GPT Setneg gagal (ReadTimeout).") from timeout

        runtime = Runtime()
        events = []
        parsed = parse_schema_ddl(b"CREATE TABLE `a` (`id` INT);\nCREATE TABLE `b` (`id` INT);")
        with self.assertRaises(AuditError):
            await audit_ddl(parsed, runtime,
                            on_event=lambda kind, message: events.append((kind, message)))
        self.assertEqual(runtime.calls, [["a", "b"]])
        self.assertTrue(any(kind == "failed" and "batch 1/1" in message
                            and "ReadTimeout" in message for kind, message in events))
        self.assertFalse(any("dipecah" in message for _, message in events))

    async def test_failed_batch_is_recorded_with_its_number(self):
        class Runtime:
            def generate_response(self, _system, _user):
                raise TelkomRuntimeError("ReadTimeout")

        events = []
        parsed = parse_schema_ddl(b"CREATE TABLE `pegawai` (`id` INT);")
        with self.assertRaises(AuditError):
            await audit_ddl(parsed, Runtime(), on_event=lambda kind, message: events.append((kind, message)))
        self.assertTrue(any(kind == "failed" and "batch 1/1" in message
                            and "ReadTimeout" in message for kind, message in events))

    async def test_truncated_audit_response_retries_instead_of_publishing_partial_result(self):
        finding = {
            "No": 1, "Nama Database": "db", "Nama Tabel": "pegawai",
            "Objek Temuan": "kolom", "Aturan Playbook/UU": "aturan",
            "Uraian Ketidaksesuaian": "uraian", "Solusi": "solusi",
            "Status": "To Do", "Catatan": "-",
        }

        class Runtime:
            def __init__(self):
                self.calls = 0

            def generate_response(self, _system, _user):
                self.calls += 1
                if self.calls == 1:
                    return "[" + json.dumps(finding) + ', {"No": 2'
                return json.dumps([finding])

        runtime = Runtime()
        events = []
        parsed = parse_schema_ddl(
            b"CREATE TABLE `db`.`pegawai` (`id` INT);"
        )
        with patch("features.audit_db.audit.perbaiki_respons_json", new_callable=AsyncMock, return_value=None):
            result = await audit_ddl(parsed, runtime, on_event=lambda kind, message: events.append((kind, message)))
        self.assertEqual(runtime.calls, 2)
        self.assertEqual(len(result), 1)
        self.assertTrue(any(kind == "retry" and "batch 1/1" in message for kind, message in events))
        self.assertTrue(any(kind == "completed" and "batch 1/1" in message for kind, message in events))


if __name__ == "__main__":
    unittest.main()
