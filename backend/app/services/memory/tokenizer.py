import hashlib
import re
import string
from collections import Counter

try:
    import jieba
except ImportError:  # pragma: no cover - exercised only when optional dep is absent
    jieba = None  # type: ignore[assignment]


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "when",
    "this",
    "that",
    "into",
    "from",
    "用户",
    "偏好",
    "当前",
    "一个",
    "以及",
    "进行",
    "需要",
    "策略",
}
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]+")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
PUNCTUATION = set(string.punctuation) | {
    "，",
    "。",
    "；",
    "：",
    "、",
    "！",
    "？",
    "（",
    "）",
    "【",
    "】",
    "《",
    "》",
    "“",
    "”",
    "‘",
    "’",
}


def normalize_content(content: str) -> str:
    return " ".join(content.strip().lower().split())


def content_hash(content: str) -> str:
    normalized = normalize_content(content)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def tokenize_text(content: str, max_keywords: int = 24) -> list[str]:
    normalized = normalize_content(content)
    if not normalized:
        return []

    tokens: list[str] = []
    tokens.extend(_tokenize_latin(normalized))
    tokens.extend(_tokenize_chinese(normalized))

    filtered = [
        token
        for token in tokens
        if _is_useful_token(token)
    ]
    counts = Counter(filtered)
    ordered = sorted(counts, key=lambda token: (-counts[token], filtered.index(token), token))
    return ordered[:max_keywords]


def jaccard_similarity(left: list[str] | set[str], right: list[str] | set[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def _tokenize_latin(content: str) -> list[str]:
    return [match.group(0).lower() for match in WORD_RE.finditer(content)]


def _tokenize_chinese(content: str) -> list[str]:
    segments = CHINESE_RE.findall(content)
    tokens: list[str] = []
    for segment in segments:
        if jieba is not None:
            tokens.extend(token.strip() for token in jieba.lcut(segment))
        tokens.extend(_chinese_ngrams(segment))
    return tokens


def _chinese_ngrams(segment: str) -> list[str]:
    tokens: list[str] = []
    for size in (2, 3):
        if len(segment) < size:
            continue
        tokens.extend(segment[index : index + size] for index in range(len(segment) - size + 1))
    return tokens


def _is_useful_token(token: str) -> bool:
    if not token:
        return False
    token = token.strip().lower()
    if token in STOP_WORDS or token in PUNCTUATION:
        return False
    if len(token) < 2 and not token.isdigit():
        return False
    return any(char.isalnum() or "\u4e00" <= char <= "\u9fff" for char in token)
