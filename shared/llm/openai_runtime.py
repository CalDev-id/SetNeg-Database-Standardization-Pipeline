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


class OpenAIEmptyResponseError(OpenAIRuntimeError):
    def __init__(self, message: str, finish_reason: Optional[str] = None) -> None:
        super().__init__(message)
        self.finish_reason = finish_reason


class OpenAIRuntime:
    """Adapter sederhana untuk API Chat Completions OpenAI."""

    provider_name = "GPT Setneg"
    api_key_env = "OPENAI_API_KEY"
    base_url_env = "OPENAI_BASE_URL"
    default_base_url = "https://api.openai.com/v1"
    model_env = "OPENAI_MODEL"
    default_model = "gpt-6-luna"
    token_parameter = "max_completion_tokens"
    allow_reasoning_retries = True
    max_attempts = 5
    max_tables_per_batch = 5
    max_completion_tokens = 20000
    reasoning_effort: Optional[str] = None
    timeout_seconds = 120
    retryable_statuses = {429, 500, 502, 503, 504, 524}

    def __init__(self, model: Optional[str] = None) -> None:
        load_dotenv()
        self.api_key = os.getenv(self.api_key_env)
        if not self.api_key:
            raise ValueError(f"{self.api_key_env} belum tersedia di environment.")

        base_url = os.getenv(self.base_url_env, self.default_base_url).rstrip("/")
        self.url = f"{base_url}/chat/completions"
        self.model = model or os.getenv(self.model_env, self.default_model)

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
            self.token_parameter: self.max_completion_tokens,
        }
        if self.reasoning_effort is not None:
            payload["reasoning_effort"] = self.reasoning_effort
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
                response_data = response.json()
                if not isinstance(response_data, dict):
                    raise TypeError(f"Respons {self.provider_name} bukan objek JSON.")
                usage = response_data.get("usage")
                if isinstance(usage, dict):
                    details = usage.get("prompt_tokens_details")
                    logger.info(
                        f"{self.provider_name} usage model=%s input=%s cached=%s output=%s",
                        self.model, usage.get("prompt_tokens"),
                        details.get("cached_tokens") if isinstance(details, dict) else None,
                        usage.get("completion_tokens"),
                    )
                choice = response_data["choices"][0]
                content = choice["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    finish_reason = choice.get("finish_reason")
                    completion_details = usage.get("completion_tokens_details") if isinstance(usage, dict) else None
                    logger.warning(
                        f"{self.provider_name} respons kosong model=%s finish_reason=%s output=%s reasoning=%s",
                        self.model, finish_reason,
                        usage.get("completion_tokens") if isinstance(usage, dict) else None,
                        completion_details.get("reasoning_tokens") if isinstance(completion_details, dict) else None,
                    )
                    if finish_reason != "length" and attempt < self.max_attempts - 1:
                        time.sleep(self._retry_delay(response, attempt))
                        continue
                    message = f"{self.provider_name} kehabisan batas token respons." if finish_reason == "length" \
                        else f"{self.provider_name} mengembalikan respons kosong."
                    raise OpenAIEmptyResponseError(message, finish_reason)
                return content.strip()
            except OpenAIRuntimeError:
                raise
            except requests.RequestException as error:
                if attempt < self.max_attempts - 1 and not isinstance(error, requests.HTTPError):
                    time.sleep(self._retry_delay(response, attempt))
                    continue
                if isinstance(error, requests.HTTPError):
                    raise OpenAIRuntimeError(
                        f"{self.provider_name} mengembalikan HTTP {error.response.status_code}."
                    ) from error
                if isinstance(error, requests.ReadTimeout):
                    raise OpenAIRuntimeError(f"{self.provider_name} melewati batas waktu respons (ReadTimeout).") from error
                raise OpenAIRuntimeError(
                    f"Koneksi ke {self.provider_name} gagal ({type(error).__name__})."
                ) from error
            except (ValueError, KeyError, IndexError, TypeError) as error:
                raise OpenAIRuntimeError(f"Format respons {self.provider_name} tidak dikenali.") from error

        raise OpenAIRuntimeError(f"{self.provider_name} gagal memproses permintaan.")


class NutaralineRuntime(OpenAIRuntime):
    provider_name = "Nutaraline"
    api_key_env = "NUTARALINE_API_KEY"
    base_url_env = "NUTARALINE_BASE_URL"
    default_base_url = "https://nutaraline.co.uk/v1"
    model_env = "NUTARALINE_MODEL"
    default_model = "deepseek-v4.1-flash-1017"
    token_parameter = "max_tokens"
    allow_reasoning_retries = False
    max_attempts = 1
    max_completion_tokens = 30000
    timeout_seconds = (10, 300)
