"""Runtime OpenAI untuk model GPT Setneg."""

import logging
import os
import time
from typing import Optional

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class OpenAIRuntimeError(RuntimeError):
    pass


class OpenAIRuntime:
    """Adapter sederhana untuk API Chat Completions OpenAI."""

    max_attempts = 5
    max_tables_per_batch = 3
    timeout_seconds = 120
    retryable_statuses = {429, 500, 502, 503, 504}

    def __init__(self, model: Optional[str] = None) -> None:
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY belum tersedia di environment.")

        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.url = f"{base_url}/chat/completions"
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-6-luna")

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
            "max_completion_tokens": 15000,
        }
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self.max_attempts):
            response: Optional[requests.Response] = None
            try:
                response = requests.post(
                    self.url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                if response.status_code in self.retryable_statuses and attempt < self.max_attempts - 1:
                    time.sleep(self._retry_delay(response, attempt))
                    continue
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise OpenAIRuntimeError("GPT Setneg mengembalikan respons kosong.")
                return content.strip()
            except OpenAIRuntimeError:
                raise
            except requests.RequestException as error:
                if attempt < self.max_attempts - 1 and not isinstance(error, requests.HTTPError):
                    time.sleep(self._retry_delay(response, attempt))
                    continue
                if isinstance(error, requests.HTTPError):
                    raise OpenAIRuntimeError(
                        f"GPT Setneg mengembalikan HTTP {error.response.status_code}."
                    ) from error
                raise OpenAIRuntimeError("Koneksi ke GPT Setneg gagal.") from error
            except (ValueError, KeyError, IndexError, TypeError) as error:
                raise OpenAIRuntimeError("Format respons GPT Setneg tidak dikenali.") from error

        raise OpenAIRuntimeError("GPT Setneg gagal memproses permintaan.")
