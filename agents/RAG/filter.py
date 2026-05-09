import re


COMMON_GREETINGS = {
    "hi", "hello", "hey", "ok", "okay", "yes", "no", "thanks", "thank you",
    "bye", "goodbye", "see you", "sure", "cool", "nice", "good", "fine",
    "hola", "adiós", "chao", "sí", "gracias", "vale", "bien",
    "bueno", "claro", "perfecto",
    "你好", "你好吗", "再见", "谢谢", "谢谢你", "好的", "是", "不是",
    "对", "不对", "嗯",
}

_CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')
_PUNCT_RE = re.compile(r'[^\w\s]')


def normalize_text(text: str) -> str:
    return _PUNCT_RE.sub('', text.strip().lower())


def contains_chinese(text: str) -> bool:
    return bool(_CHINESE_RE.search(text))


def is_common_greeting(text: str) -> bool:
    return normalize_text(text) in COMMON_GREETINGS


def should_embed(text: str) -> bool:
    if not text or not text.strip():
        return False
    if is_common_greeting(text):
        return False
    if contains_chinese(text):
        return True
    if len(text.strip()) < 10:
        return False
    return True
