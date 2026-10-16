import logging
import os
import time

import requests
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


class GroqRuntimeError(RuntimeError):
    pass


class GroqPayloadTooLargeError(GroqRuntimeError):
    pass


class GroqRuntime:
    models = (
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
    )
    max_tables_per_batch = 5
    max_input_characters = 12_000
    timeout_seconds = 120
    max_rate_limit_retries = 2

    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY belum tersedia di environment.")
        self.url = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        self.model = self.models[0]
        self._retry_models = None

    @staticmethod
    def _retry_delay(response: requests.Response) -> float:
        try:
            return min(30, max(1, float(response.headers.get("Retry-After", 1))))
        except (TypeError, ValueError):
            return 1

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        models = self._retry_models or self.models
        self._retry_models = None
        errors = []
        for retry in range(self.max_rate_limit_retries + 1):
            retry_delays = []
            for model in models:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "max_completion_tokens": 10000,
                }
                try:
                    response = requests.post(
                        self.url, headers=headers, json=payload, timeout=self.timeout_seconds,
                    )
                    if response.status_code == 429:
                        retry_delays.append(self._retry_delay(response))
                        errors.append(f"{model}: Groq mengembalikan HTTP 429.")
                        logger.warning("Model Groq %s terkena limit; mencoba model berikutnya.", model)
                        continue
                    if response.status_code == 413:
                        raise GroqPayloadTooLargeError(
                            "Payload request melebihi batas ukuran Groq."
                        )
                    if response.status_code >= 400:
                        raise GroqRuntimeError(f"Groq mengembalikan HTTP {response.status_code}.")
                    content = response.json()["choices"][0]["message"]["content"]
                    if not isinstance(content, str) or not content.strip():
                        raise GroqRuntimeError("Groq mengembalikan respons kosong.")
                    self.model = model
                    return content.strip()
                except GroqPayloadTooLargeError:
                    raise
                except (requests.RequestException, ValueError, KeyError, IndexError, TypeError, GroqRuntimeError) as error:
                    errors.append(f"{model}: {error}")
                    logger.warning("Model Groq %s gagal; mencoba model berikutnya.", model)
            if retry_delays and retry < self.max_rate_limit_retries:
                delay = max(retry_delays)
                logger.warning("Seluruh model Groq terkena limit; mencoba lagi dalam %.0f detik.", delay)
                time.sleep(delay)
                continue
            break
        raise GroqRuntimeError("Seluruh model Groq gagal: " + " ".join(errors))

    def use_fallback_model(self) -> bool:
        try:
            next_index = self.models.index(self.model) + 1
            self._retry_models = self.models[next_index:next_index + 1]
        except ValueError:
            self._retry_models = None
        if not self._retry_models:
            return False
        logger.warning("Respons model Groq ditolak; retry memakai %s.", self._retry_models[0])
        return True
