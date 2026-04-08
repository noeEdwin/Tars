import json
from pathlib import Path
from thefuzz import fuzz

def is_phonetically_similar(target: str, user_input: str) -> bool:
    """True when fuzz ratio > 80 AND the strings share at least one character."""
    if not target or not user_input:
        return False
    if not any(c in user_input for c in target):
        return False
    ratio = fuzz.partial_ratio(target.lower(), user_input.lower())
    return ratio > 80

def load_lesson_json(lesson_id: int) -> dict:
    try:
        base_path = Path(__file__).resolve().parent.parent.parent
        file_path = base_path / "data_normal_mode" / "data" / f"leccion_{lesson_id}.json"
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"vocabulary": [{"zh": "你好", "py": "nǐ hǎo", "es": "hola"}]}