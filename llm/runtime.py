from llm.gemini_runtime import GeminiRuntime
from llm.telkom_gpt_runtime import GPTRunTime

def get_runtime(model: str):
    if model == "telkom":
        return GPTRunTime()
    if model == "gemini":
        return GeminiRuntime()
    raise ValueError("Model analisis tidak dikenal.")
