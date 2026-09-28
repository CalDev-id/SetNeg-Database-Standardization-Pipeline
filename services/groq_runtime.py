import os

from dotenv import load_dotenv
from groq import Groq


class GroqRuntime:

    def __init__(self, model: str = "qwen/qwen3.8-27b") -> None:
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY belum tersedia di environment.")

        self.model = model
        self.client = Groq(api_key=api_key)

    def generate_response(self, system_prompt: str, user_prompt: str, **options):
        max_completion_tokens = options.pop("max_completion_tokens", 800)
        return self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_completion_tokens=max_completion_tokens,
            **options,
        )
