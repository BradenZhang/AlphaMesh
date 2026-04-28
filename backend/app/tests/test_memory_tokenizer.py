from app.services.memory.tokenizer import content_hash, tokenize_text


def test_tokenizer_extracts_chinese_keywords() -> None:
    tokens = tokenize_text("用户偏好低回撤策略，关注估值安全边际和现金流。")

    assert "低回撤" in tokens or "回撤" in tokens
    assert "估值" in tokens
    assert "现金流" in tokens or "现金" in tokens


def test_tokenizer_keeps_latin_words_and_symbols() -> None:
    tokens = tokenize_text("AAPL research prefers free-cash-flow and ROE above 20.")

    assert "aapl" in tokens
    assert "research" in tokens
    assert "roe" in tokens


def test_content_hash_uses_normalized_content() -> None:
    left = content_hash(" Prefer   low drawdown ")
    right = content_hash("prefer low drawdown")

    assert left == right
