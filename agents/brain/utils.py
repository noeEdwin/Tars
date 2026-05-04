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
        file_path = base_path / "data_normal_mode" / "data" / "tars_150_hsk1.json"
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_vocab = data["modulos_de_aprendizaje"][0]["vocabulario"]
        transformed_vocab = [
            {"zh": item["palabra"], "py": item["pinyin"], "es": item["significado"]}
            for item in raw_vocab
        ]
        return {"vocabulary": transformed_vocab}
    except Exception:
        return {"vocabulary": [{"zh": "你好", "py": "nǐ hǎo", "es": "hola"}]}