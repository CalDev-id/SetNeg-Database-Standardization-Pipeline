import os
import time
from typing import Optional

import requests
from dotenv import load_dotenv


class GeminiRuntimeError(RuntimeError):
    pass


class GeminiRuntime:
    max_attempts = 3
    max_tables_per_batch = 5
    timeout_seconds = 300
    retryable_statuses = {500, 502, 503, 504}
    retry_batch_size = 8
    MODEL_FALLBACKS = (
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
    )

    def __init__(self, model: Optional[str] = None) -> None:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY belum tersedia di environment.")

        self.api_key = api_key
        selected_model = model or os.getenv("GEMINI_MODEL", self.MODEL_FALLBACKS[0])
        if selected_model in self.MODEL_FALLBACKS:
            start = self.MODEL_FALLBACKS.index(selected_model)
            self.models = self.MODEL_FALLBACKS[start:]
        else:
            self.models = (selected_model,)
        self.model = self.models[0]

    @staticmethod
    def _url(model: str) -> str:
        return (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        statuses: list[int] = []
        for index, model in enumerate(self.models):
            for attempt in range(self.max_attempts):
                try:
                    response = requests.post(
                        self._url(model),
                        headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
                        json={
                            "systemInstruction": {"parts": [{"text": system_prompt}]},
                            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                            "generationConfig": {
                                "temperature": 0.1,
                                "maxOutputTokens": 10000,
                                "responseMimeType": "application/json",
                            },
                        },
                        timeout=self.timeout_seconds,
                    )
                except requests.RequestException as error:
                    if attempt < self.max_attempts - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise GeminiRuntimeError(
                        f"Koneksi ke Gemini gagal ({type(error).__name__})."
                    ) from error

                statuses.append(response.status_code)
                if response.status_code == 429:
                    break
                if response.status_code in self.retryable_statuses:
                    if attempt < self.max_attempts - 1:
                        time.sleep(2 ** attempt)
                        continue
                    break
                try:
                    response.raise_for_status()
                    content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                except requests.HTTPError as error:
                    raise GeminiRuntimeError(
                        f"Gemini mengembalikan HTTP {response.status_code}."
                    ) from error
                except (ValueError, KeyError, IndexError, TypeError) as error:
                    raise GeminiRuntimeError("Format respons Gemini tidak dikenali.") from error

                if not isinstance(content, str) or not content.strip():
                    raise GeminiRuntimeError("Gemini mengembalikan respons kosong.")
                self.model = model
                self.models = self.models[index:]
                return content.strip()

        if statuses and all(status == 429 for status in statuses):
            raise GeminiRuntimeError("Seluruh model Gemini mencapai batas permintaan.")
        if statuses and all(status in self.retryable_statuses for status in statuses):
            raise GeminiRuntimeError("Seluruh model Gemini sementara tidak tersedia.")
        raise GeminiRuntimeError("Gemini gagal memproses permintaan.")
