"""Pemilihan runtime LLM lintas fitur."""

from shared.llm.gemini_runtime import GeminiRuntime
from shared.llm.openai_runtime import NutaralineRuntime, OpenAIRuntime
from shared.llm.telkom_gpt_runtime import GPTRunTime

def get_runtime(model: str):
    if model == "telkom":
        return GPTRunTime()
    if model == "gemini":
        return GeminiRuntime()
    if model == "gpt_setneg":
        return OpenAIRuntime()
    if model == "nutaraline":
        return NutaralineRuntime()
    raise ValueError("Model analisis tidak dikenal.")
