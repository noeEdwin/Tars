import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.RAG.filter import normalize_text, contains_chinese, is_common_greeting, should_embed


def test_normalize_text():
    assert normalize_text("Hello, World!") == "hello world"
    assert normalize_text("  你好  ") == "你好"
    assert normalize_text("OK?") == "ok"
    assert normalize_text("") == ""
    print("  normalize_text: PASS")


def test_contains_chinese():
    assert contains_chinese("你好") is True
    assert contains_chinese("hello 世界") is True
    assert contains_chinese("hello world") is False
    assert contains_chinese("hola") is False
    print("  contains_chinese: PASS")


def test_is_common_greeting():
    assert is_common_greeting("hello") is True
    assert is_common_greeting("Hello!") is True
    assert is_common_greeting("hola") is True
    assert is_common_greeting("你好") is True
    assert is_common_greeting("thanks") is True
    assert is_common_greeting("I am learning Chinese") is False
    assert is_common_greeting("我是老师") is False
    print("  is_common_greeting: PASS")


def test_should_embed():
    assert should_embed("hello") is False
    assert should_embed("ok") is False
    assert should_embed("hola") is False
    assert should_embed("你好") is False
    assert should_embed("我是老师") is True
    assert should_embed("hi") is False
    assert should_embed("short") is False
    assert should_embed("This is a longer English sentence") is True
    assert should_embed("") is False
    assert should_embed("   ") is False
    assert should_embed("谢谢") is False
    assert should_embed("好的") is False
    assert should_embed("我喜欢学中文因为很有趣") is True
    print("  should_embed: PASS")


if __name__ == "__main__":
    print("Running filter tests...")
    test_normalize_text()
    test_contains_chinese()
    test_is_common_greeting()
    test_should_embed()
    print("All tests passed.")
