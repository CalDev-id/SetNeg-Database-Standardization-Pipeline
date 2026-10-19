"""Pemilihan runtime LLM lintas fitur."""

from shared.llm.gemini_runtime import GeminiRuntime
from shared.llm.telkom_gpt_runtime import GPTRunTime

def get_runtime(model: str):
    if model == "telkom":
        return GPTRunTime()
    if model == "gemini":
        return GeminiRuntime()
    raise ValueError("Model analisis tidak dikenal.")
