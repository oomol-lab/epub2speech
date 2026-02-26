import re
from dataclasses import dataclass
from html.parser import HTMLParser

TEXT_CLEANING_STRICTNESS_LEVELS: tuple[str, ...] = ("conservative", "balanced", "aggressive")

_BLOCK_ELEMENTS: tuple[str, ...] = ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "br", "hr")
_HEADING_ELEMENTS: tuple[str, ...] = ("h1", "h2", "h3", "h4", "h5", "h6")
_BLACKLIST_TAGS: tuple[str, ...] = (
    "script",
    "style",
    "noscript",
    "iframe",
    "object",
    "embed",
    "param",
    "source",
    "track",
    "canvas",
    "svg",
    "math",
    "template",
    "slot",
)

_TOC_HEADER_RE = re.compile(r"^(目录|目次|contents?|table of contents)$", re.IGNORECASE)
_DECORATION_RE = re.compile(r"^[_\-=~*#·.•⋯…]{3,}$")
_PAGE_NUMBER_RE = re.compile(r"^(?:page\s*)?\d{1,4}$", re.IGNORECASE)
_TOC_LEADER_RE = re.compile(r"^.{1,120}(?:\.{2,}|_{2,}|-{2,}|…{2,}|·{2,}|⋯{2,})\s*\d{1,4}$")
_TOC_ENTRY_ZH_RE = re.compile(
    r"^第?[0-9一二三四五六七八九十百千万零〇两]+[章节卷部篇回]\s*.*(?:\.{2,}|_{2,}|-{2,}|…{2,}|·{2,}|⋯{2,})\s*\d{1,4}$"
)
_TOC_ENTRY_EN_RE = re.compile(
    r"^(chapter|section|part|book|appendix)\b.*(?:\.{2,}|_{2,}|-{2,}|…{2,}|·{2,}|⋯{2,})\s*\d{1,4}$",
    re.IGNORECASE,
)
_LIKELY_TOC_SHORT_EN_RE = re.compile(r"^(chapter|section|part|book)\s+([ivxlcdm]+|\d+)\b", re.IGNORECASE)
_WRAPPER_SIDE_PATTERN = r"[-_=~*#]{2,}"
_GENERIC_WRAPPED_MARKER_RE = re.compile(
    rf"{_WRAPPER_SIDE_PATTERN}\s*(正文|简介|内容简介|正文开始)\s*{_WRAPPER_SIDE_PATTERN}"
)
_ANY_WRAPPED_DECORATION_RE = re.compile(rf"{_WRAPPER_SIDE_PATTERN}\s*([^\n]{{1,80}}?)\s*{_WRAPPER_SIDE_PATTERN}")
_BOOK_TITLE_IN_PARENS_RE = re.compile(r"[（(]\s*《([^》]{1,120})》\s*[）)]")
_PUNCT_RE = re.compile(r"[。！？!?;；:,，.]")
_WORD_RE = re.compile(r"[A-Za-z]+")
_ZH_STOPWORD_HINTS = (
    "的",
    "了",
    "是",
    "在",
    "和",
    "与",
    "及",
    "并",
    "而",
    "但",
    "如果",
    "因为",
    "所以",
    "我们",
    "他们",
    "你们",
    "这",
    "那",
)
_EN_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "if",
    "then",
    "than",
    "to",
    "of",
    "for",
    "on",
    "in",
    "at",
    "by",
    "with",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "it",
    "this",
    "that",
    "these",
    "those",
    "as",
    "from",
    "we",
    "you",
    "they",
    "he",
    "she",
}
_GENERIC_WRAPPER_MARKERS = {
    "正文",
    "简介",
    "内容简介",
    "正文开始",
}


@dataclass(frozen=True)
class _StrictnessConfig:
    short_length: int
    low_length: int
    high_length: int
    max_link_density: float
    min_punct_density: float
    min_stopword_density: float
    good_score: float
    bad_score: float


_STRICTNESS_CONFIGS: dict[str, _StrictnessConfig] = {
    "conservative": _StrictnessConfig(
        short_length=18,
        low_length=60,
        high_length=180,
        max_link_density=0.55,
        min_punct_density=0.003,
        min_stopword_density=0.005,
        good_score=0.5,
        bad_score=-2.5,
    ),
    "balanced": _StrictnessConfig(
        short_length=25,
        low_length=70,
        high_length=200,
        max_link_density=0.35,
        min_punct_density=0.004,
        min_stopword_density=0.008,
        good_score=1.0,
        bad_score=-2.0,
    ),
    "aggressive": _StrictnessConfig(
        short_length=35,
        low_length=80,
        high_length=220,
        max_link_density=0.25,
        min_punct_density=0.005,
        min_stopword_density=0.01,
        good_score=1.2,
        bad_score=-1.5,
    ),
}


@dataclass
class _Block:
    index: int
    tag: str
    text: str
    total_chars: int
    link_chars: int
    is_heading: bool
    keep: bool = False
    classification: str = "short"
    reason: str = ""
    score: float = 0.0
    link_density: float = 0.0
    punct_density: float = 0.0
    stopword_density: float = 0.0


class _BlockExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._blacklist_depth = 0
        self._link_depth = 0
        self._blocks: list[_Block] = []
        self._current_block: _Block | None = None

    def _start_block(self, tag: str) -> None:
        self._finish_block()
        self._current_block = _Block(
            index=len(self._blocks),
            tag=tag,
            text="",
            total_chars=0,
            link_chars=0,
            is_heading=tag in _HEADING_ELEMENTS,
        )

    def _finish_block(self) -> None:
        if self._current_block is None:
            return
        cleaned = re.sub(r"\s+", " ", self._current_block.text).strip()
        if cleaned:
            self._current_block.text = cleaned
            self._current_block.total_chars = max(self._current_block.total_chars, len(cleaned))
            self._blocks.append(self._current_block)
        self._current_block = None

    def handle_starttag(self, tag, attrs):
        _ = attrs
        normalized_tag = tag.lower()
        if normalized_tag in _BLACKLIST_TAGS:
            self._blacklist_depth += 1
            return
        if self._blacklist_depth > 0:
            return
        if normalized_tag == "a":
            self._link_depth += 1
        if normalized_tag in _BLOCK_ELEMENTS:
            self._start_block(normalized_tag)

    def handle_endtag(self, tag):
        normalized_tag = tag.lower()
        if normalized_tag in _BLACKLIST_TAGS and self._blacklist_depth > 0:
            self._blacklist_depth -= 1
            return
        if self._blacklist_depth > 0:
            return
        if normalized_tag == "a" and self._link_depth > 0:
            self._link_depth -= 1
        if normalized_tag in _BLOCK_ELEMENTS and self._current_block is not None:
            self._finish_block()

    def handle_data(self, data):
        if self._blacklist_depth > 0:
            return
        clean_data = re.sub(r"\s+", " ", data).strip()
        if not clean_data:
            return
        if self._current_block is None:
            self._start_block("text")
        assert self._current_block is not None
        if self._current_block.text:
            self._current_block.text += " "
        self._current_block.text += clean_data
        text_len = len(clean_data)
        self._current_block.total_chars += text_len
        if self._link_depth > 0:
            self._current_block.link_chars += text_len

    def get_blocks(self) -> list[_Block]:
        self._finish_block()
        return self._blocks


def _validate_cleaning_strictness(cleaning_strictness: str) -> None:
    if cleaning_strictness not in TEXT_CLEANING_STRICTNESS_LEVELS:
        raise ValueError(f"Unsupported cleaning strictness: {cleaning_strictness}")


def _is_noise_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True

    compact_line = re.sub(r"\s+", " ", stripped)
    if _TOC_HEADER_RE.fullmatch(compact_line):
        return True
    if _DECORATION_RE.fullmatch(compact_line):
        return True
    if _PAGE_NUMBER_RE.fullmatch(compact_line):
        return True
    if _TOC_LEADER_RE.fullmatch(compact_line):
        return True
    if _TOC_ENTRY_ZH_RE.fullmatch(compact_line):
        return True
    if _TOC_ENTRY_EN_RE.fullmatch(compact_line):
        return True
    return False


def _estimate_stopword_density(text: str) -> float:
    word_matches = _WORD_RE.findall(text.lower())
    en_density = 0.0
    if word_matches:
        en_hits = sum(1 for token in word_matches if token in _EN_STOPWORDS)
        en_density = en_hits / len(word_matches)

    zh_hits = sum(text.count(word) for word in _ZH_STOPWORD_HINTS)
    zh_density = zh_hits / max(len(text), 1)
    return max(en_density, zh_density)


def _english_word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _normalize_wrapped_decoration_text(text: str) -> tuple[str, bool]:
    had_change = False

    replaced = _GENERIC_WRAPPED_MARKER_RE.sub(" ", text)
    if replaced != text:
        had_change = True
    text = replaced

    def _replace_wrapped(match: re.Match[str]) -> str:
        nonlocal had_change
        inner = re.sub(r"\s+", " ", match.group(1)).strip()
        if not inner or inner in _GENERIC_WRAPPER_MARKERS:
            had_change = True
            return " "
        had_change = True
        return f" {inner} "

    text = _ANY_WRAPPED_DECORATION_RE.sub(_replace_wrapped, text)
    text = re.sub(r"\s+", " ", text).strip()
    return text, had_change


def _normalize_tts_punctuation_text(text: str) -> str:
    # Keep book title semantics but strip redundant outer parentheses for TTS stability.
    normalized = _BOOK_TITLE_IN_PARENS_RE.sub(r"《\1》", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _classify_block(block: _Block, config: _StrictnessConfig) -> None:
    text, had_wrapped_change = _normalize_wrapped_decoration_text(block.text)
    text = _normalize_tts_punctuation_text(text)
    block.text = text
    if had_wrapped_change and not text:
        block.classification = "bad"
        block.reason = "decorative_wrapper_marker"
        block.score = -10.0
        return

    char_len = len(text)
    block.link_density = block.link_chars / max(block.total_chars, 1)
    punct_count = len(_PUNCT_RE.findall(text))
    block.punct_density = punct_count / max(char_len, 1)
    block.stopword_density = _estimate_stopword_density(text)

    score = 0.0
    reason = "content_like"
    if _is_noise_line(text):
        block.classification = "bad"
        block.reason = "noise_pattern"
        block.score = -10.0
        return

    if char_len >= config.high_length:
        score += 2.0
    elif char_len >= config.low_length:
        score += 1.0

    if block.link_density > config.max_link_density:
        score -= 2.0
        reason = "high_link_density"
    if block.punct_density < config.min_punct_density and char_len >= config.low_length:
        score -= 1.0
        reason = "low_punctuation_density"
    if block.stopword_density >= config.min_stopword_density:
        score += 0.5
    if re.search(r"[。！？!?]", text):
        score += 0.5
    if block.is_heading:
        score += 0.3

    block.score = score
    block.reason = reason
    if char_len < config.short_length:
        block.classification = "short"
    elif score >= config.good_score:
        block.classification = "good"
    elif score <= config.bad_score:
        block.classification = "bad"
    else:
        block.classification = "near_good"


def _apply_context_reclassification(blocks: list[_Block], cleaning_strictness: str) -> None:
    for idx, block in enumerate(blocks):
        prev_cls = blocks[idx - 1].classification if idx > 0 else None
        next_cls = blocks[idx + 1].classification if idx + 1 < len(blocks) else None

        if block.classification == "short":
            if block.is_heading and next_cls in ("good", "near_good"):
                block.classification = "near_good"
                block.reason = "heading_with_content_context"
            elif prev_cls == "good" and next_cls == "good":
                block.classification = "near_good"
                block.reason = "surrounded_by_content"
            elif re.search(r"[。！？!?]", block.text) and len(block.text) >= 4:
                block.classification = "near_good"
                block.reason = "short_but_sentence_like"
            elif re.search(r"[\u4e00-\u9fff]", block.text) and len(block.text) >= 4 and not _is_noise_line(block.text):
                block.classification = "near_good"
                block.reason = "short_cjk_content_like"
            elif (
                cleaning_strictness != "aggressive"
                and _english_word_count(block.text) >= 4
                and block.stopword_density >= 0.12
                and not _LIKELY_TOC_SHORT_EN_RE.match(block.text)
            ):
                block.classification = "near_good"
                block.reason = "short_en_content_like"
            elif (
                cleaning_strictness != "aggressive"
                and next_cls in ("good", "near_good")
                and idx + 1 < len(blocks)
                and _english_word_count(block.text) >= 2
                and _english_word_count(f"{block.text} {blocks[idx + 1].text}") >= 6
                and not _LIKELY_TOC_SHORT_EN_RE.match(block.text)
            ):
                block.classification = "near_good"
                block.reason = "short_prefix_for_content"
            elif (
                cleaning_strictness != "aggressive"
                and prev_cls in ("good", "near_good")
                and idx > 0
                and _english_word_count(block.text) >= 2
                and _english_word_count(f"{blocks[idx - 1].text} {block.text}") >= 6
                and not _LIKELY_TOC_SHORT_EN_RE.match(block.text)
            ):
                block.classification = "near_good"
                block.reason = "short_suffix_for_content"
            elif cleaning_strictness == "conservative":
                block.classification = "near_good"
                block.reason = "conservative_short_keep"

        if block.classification == "near_good":
            if prev_cls in ("good", "near_good") and next_cls in ("good", "near_good"):
                block.classification = "good"
                block.reason = "context_promoted"

    # Second pass: include short prefix/suffix fragments around already promoted content blocks.
    if cleaning_strictness != "aggressive":
        for idx, block in enumerate(blocks):
            if block.classification != "short":
                continue
            prev_cls = blocks[idx - 1].classification if idx > 0 else None
            next_cls = blocks[idx + 1].classification if idx + 1 < len(blocks) else None

            if (
                next_cls in ("good", "near_good")
                and idx + 1 < len(blocks)
                and _english_word_count(block.text) >= 2
                and _english_word_count(f"{block.text} {blocks[idx + 1].text}") >= 6
                and not _LIKELY_TOC_SHORT_EN_RE.match(block.text)
            ):
                block.classification = "near_good"
                block.reason = "short_prefix_for_content"
                continue

            if (
                prev_cls in ("good", "near_good")
                and idx > 0
                and _english_word_count(block.text) >= 2
                and _english_word_count(f"{blocks[idx - 1].text} {block.text}") >= 6
                and not _LIKELY_TOC_SHORT_EN_RE.match(block.text)
            ):
                block.classification = "near_good"
                block.reason = "short_suffix_for_content"


def _finalize_keep_decision(blocks: list[_Block], cleaning_strictness: str) -> None:
    for block in blocks:
        if block.classification == "good":
            block.keep = True
            continue
        if block.classification == "near_good":
            if cleaning_strictness == "aggressive" and block.reason in ("high_link_density", "low_punctuation_density"):
                block.keep = False
            else:
                block.keep = True
            continue
        block.keep = False


def _serialize_report(blocks: list[_Block], cleaning_strictness: str) -> dict:
    removed_blocks = [block for block in blocks if not block.keep]
    kept_blocks = [block for block in blocks if block.keep]

    removed_samples = []
    for block in removed_blocks[:20]:
        removed_samples.append(
            {
                "index": block.index,
                "tag": block.tag,
                "text": block.text[:200],
                "classification": block.classification,
                "reason": block.reason,
                "score": round(block.score, 3),
                "link_density": round(block.link_density, 3),
                "punct_density": round(block.punct_density, 3),
                "stopword_density": round(block.stopword_density, 3),
            }
        )

    return {
        "strictness": cleaning_strictness,
        "total_blocks": len(blocks),
        "kept_blocks": len(kept_blocks),
        "removed_blocks": len(removed_blocks),
        "removed_samples": removed_samples,
    }


def _clean_with_block_pipeline(text_blocks: list[_Block], cleaning_strictness: str) -> tuple[str, dict]:
    config = _STRICTNESS_CONFIGS[cleaning_strictness]

    for block in text_blocks:
        _classify_block(block, config)
    _apply_context_reclassification(text_blocks, cleaning_strictness)
    _finalize_keep_decision(text_blocks, cleaning_strictness)

    kept_lines = [block.text for block in text_blocks if block.keep and block.text]
    cleaned_text = " ".join(kept_lines)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
    report = _serialize_report(text_blocks, cleaning_strictness)
    return cleaned_text, report


def _extract_blocks_with_html_parser(html_content: str) -> list[_Block]:
    extractor = _BlockExtractor()
    extractor.feed(html_content)
    return extractor.get_blocks()


def _extract_blocks_with_regex(html_content: str) -> list[_Block]:
    content = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL | re.IGNORECASE)

    text_parts = []
    for tag in ["title", "p", "h1", "h2", "h3", "h4", "li", "div"]:
        pattern = f"<{tag}[^>]*>(.*?)</{tag}>"
        matches = re.findall(pattern, content, flags=re.DOTALL | re.IGNORECASE)
        for match in matches:
            clean_text = re.sub(r"<[^>]+>", " ", match)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()
            if clean_text:
                text_parts.append(clean_text)

    if not text_parts:
        all_text = re.sub(r"<[^>]+>", " ", content)
        all_text = re.sub(r"\s+", " ", all_text).strip()
        if all_text:
            text_parts.append(all_text)

    blocks = []
    for index, text in enumerate(text_parts):
        blocks.append(
            _Block(
                index=index,
                tag="regex",
                text=text,
                total_chars=len(text),
                link_chars=0,
                is_heading=False,
            )
        )
    return blocks


def debug_html_content(html_content: str, max_chars: int = 1000) -> None:
    print("=== DEBUG HTML CONTENT ===")
    print(f"Content length: {len(html_content)} characters")
    print(f"First {max_chars} characters:")
    print(html_content[:max_chars])
    if len(html_content) > max_chars:
        print(f"... (truncated, total {len(html_content)} chars)")
    print("=== END DEBUG ===")


def extract_text_from_html_with_report(
    html_content: str,
    cleaning_strictness: str = "balanced",
) -> tuple[str, dict]:
    _validate_cleaning_strictness(cleaning_strictness)
    try:
        blocks = _extract_blocks_with_html_parser(html_content)
    except (ValueError, TypeError):
        blocks = _extract_blocks_with_regex(html_content)

    if not blocks:
        return "", {
            "strictness": cleaning_strictness,
            "total_blocks": 0,
            "kept_blocks": 0,
            "removed_blocks": 0,
            "removed_samples": [],
        }

    return _clean_with_block_pipeline(blocks, cleaning_strictness)


def extract_text_from_html(html_content: str, cleaning_strictness: str = "balanced") -> str:
    text, _ = extract_text_from_html_with_report(
        html_content=html_content,
        cleaning_strictness=cleaning_strictness,
    )
    return text
