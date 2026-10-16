import asyncio
from typing import Callable, Protocol, TypeVar

from shared.json_utils import JsonFormatError
from shared.llm.gemini_runtime import GeminiRuntime
from shared.llm.gemini_runtime import GeminiRuntimeError
from shared.llm.groq_runtime import GroqPayloadTooLargeError, GroqRuntime, GroqRuntimeError
from shared.llm.telkom_gpt_runtime import GPTRunTime, TelkomRuntimeError


class AuditError(RuntimeError):
    status_code = 424


class PayloadTooLargeError(AuditError):
    pass


class LlmRuntime(Protocol):
    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        ...


T = TypeVar("T")

def get_runtime(model: str):
    if model == "qwen":
        return GroqRuntime()
    if model == "telkom":
        return GPTRunTime()
    if model == "gemini":
        return GeminiRuntime()
    raise ValueError("Model analisis tidak dikenal.")


async def request_json(
    runtime: LlmRuntime, system_prompt: str, user_prompt: str,
    reader: Callable[[str], T], stage: str,
) -> T:
    for attempt in range(2):
        try:
            content = await asyncio.to_thread(runtime.generate_response, system_prompt, user_prompt)
        except GroqPayloadTooLargeError as error:
            raise PayloadTooLargeError(f"Payload terlalu besar pada tahap {stage}.") from error
        except (TelkomRuntimeError, GeminiRuntimeError, GroqRuntimeError) as error:
            raise AuditError(f"LLM gagal pada tahap {stage}: {error}") from error
        try:
            return reader(content)
        except JsonFormatError as error:
            if attempt:
                raise
            fallback_model = getattr(runtime, "use_fallback_model", None)
            if callable(fallback_model):
                fallback_model()
            user_prompt += f"\n\nRespons sebelumnya ditolak: {error} Ulangi tahap {stage} dengan JSON lengkap."
    raise AssertionError("Percobaan tahap audit tidak dijalankan.")
