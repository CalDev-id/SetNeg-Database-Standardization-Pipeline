"""Runtime Telkom GPT yang dapat dipakai lintas fitur."""

import logging
import os
import time
from typing import Optional

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class TelkomRuntimeError(RuntimeError):
    pass


class GPTRunTime:
    max_attempts = 5
    max_tables_per_batch = 3

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("TELKOM_GPT_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("TELKOM_GPT_API_KEY belum tersedia di environment.")
        self.url = os.getenv(
            "TELKOM_GPT_URL",
            "https://telkom-ai-dag.api.apilogy.id/dummy_api/0.0.0-llm-dummy/v1/llm/chat/completions",
        )
        self.model = os.getenv("TELKOM_GPT_MODEL", "llm_mini_max")

    @staticmethod
    def _retry_delay(response: Optional[requests.Response], attempt: int) -> float:
        retry_after = response.headers.get("Retry-After") if response is not None else None
        try:
            return min(30, max(1, float(retry_after)))
        except (TypeError, ValueError):
            return 2 ** (attempt + 1)

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_completion_tokens": 10000,
            "stream": False,
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }
        for attempt in range(self.max_attempts):
            try:
                response = requests.post(self.url, headers=headers, json=payload, timeout=120)
                if (
                    response.status_code in {429, 500, 502, 503, 504}
                    and attempt < self.max_attempts - 1
                ):
                    time.sleep(self._retry_delay(response, attempt))
                    continue
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    if attempt < self.max_attempts - 1:
                        logger.warning("Telkom GPT mengembalikan respons kosong, mencoba ulang.")
                        time.sleep(self._retry_delay(response, attempt))
                        continue
                    raise TelkomRuntimeError("Telkom GPT mengembalikan respons kosong.")
                return content.strip()
            except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as error:
                if (
                    isinstance(error, requests.RequestException)
                    and attempt < self.max_attempts - 1
                    and not isinstance(error, requests.HTTPError)
                ):
                    time.sleep(self._retry_delay(None, attempt))
                    continue
                logger.warning("Permintaan Telkom GPT gagal: %s", type(error).__name__)
                if isinstance(error, requests.HTTPError):
                    raise TelkomRuntimeError(
                        f"Telkom GPT mengembalikan HTTP {error.response.status_code}."
                    ) from error
                if isinstance(error, requests.RequestException):
                    raise TelkomRuntimeError("Koneksi ke Telkom GPT gagal.") from error
                raise TelkomRuntimeError("Format respons layanan Telkom GPT tidak dikenali.") from error
        raise TelkomRuntimeError("Telkom GPT gagal memproses batch.")
