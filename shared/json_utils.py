import json
from typing import Any


class JsonFormatError(ValueError):
    pass


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def baca_json(content: str) -> Any:
    content = content.strip()
    if content.startswith("```") and content.endswith("```"):
        content = "\n".join(content.splitlines()[1:-1]).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise JsonFormatError("Respons bukan JSON lengkap dan valid.") from error
