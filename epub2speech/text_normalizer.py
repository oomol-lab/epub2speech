import re

TEXT_NORMALIZATION_LEVELS: tuple[str, ...] = ("off", "basic")

_ZH_DIGITS = "零一二三四五六七八九"
_GROUP_UNITS = ("", "万", "亿", "兆")
_DATE_RE = re.compile(r"(?<!\d)(\d{4})[/-](\d{1,2})[/-](\d{1,2})(?!\d)")
_PERCENT_RE = re.compile(r"(?<!\d)(\d+(?:\.\d+)?)\s*%")
_CHAPTER_NUM_RE = re.compile(r"第\s*(\d+)\s*([章节卷部篇回集])")
_TIME_RE = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")
_CJK_CONTEXT_NUM_RE = re.compile(r"(?<=[\u4e00-\u9fff])(\d+(?:\.\d+)?)(?=[\u4e00-\u9fff])")
_MULTISPACE_RE = re.compile(r"[ \t]+")


def _four_digit_to_zh(value: int) -> str:
    assert 0 <= value <= 9999
    if value == 0:
        return ""

    digits = [value // 1000, (value // 100) % 10, (value // 10) % 10, value % 10]
    units = ("千", "百", "十", "")
    pieces: list[str] = []
    pending_zero = False

    for idx, digit in enumerate(digits):
        if digit == 0:
            if pieces and any(rest > 0 for rest in digits[idx + 1 :]):
                pending_zero = True
            continue

        if pending_zero:
            pieces.append(_ZH_DIGITS[0])
            pending_zero = False

        if units[idx] == "十" and digit == 1 and not pieces:
            pieces.append("十")
        else:
            pieces.append(_ZH_DIGITS[digit] + units[idx])

    return "".join(pieces)


def _int_to_zh(value: int) -> str:
    if value == 0:
        return _ZH_DIGITS[0]

    groups: list[int] = []
    while value > 0:
        groups.append(value % 10000)
        value //= 10000

    pieces: list[str] = []
    pending_zero = False
    for idx in range(len(groups) - 1, -1, -1):
        group = groups[idx]
        if group == 0:
            if pieces:
                pending_zero = True
            continue

        if pending_zero:
            pieces.append(_ZH_DIGITS[0])
            pending_zero = False
        elif pieces and group < 1000:
            pieces.append(_ZH_DIGITS[0])

        pieces.append(_four_digit_to_zh(group) + _GROUP_UNITS[idx])

    return "".join(pieces)


def _number_to_zh(token: str) -> str:
    token = token.strip()
    if not token:
        return token

    if token.startswith("-"):
        return "负" + _number_to_zh(token[1:])

    if "." in token:
        integer_part, frac_part = token.split(".", 1)
        integer_value = int(integer_part or "0")
        frac_digits = "".join(_ZH_DIGITS[int(ch)] for ch in frac_part if ch.isdigit())
        if not frac_digits:
            return _int_to_zh(integer_value)
        return f"{_int_to_zh(integer_value)}点{frac_digits}"

    return _int_to_zh(int(token))


def _year_to_zh(year_text: str) -> str:
    return "".join(_ZH_DIGITS[int(ch)] for ch in year_text)


def normalize_text_for_tts(text: str, level: str = "basic") -> str:
    if level not in TEXT_NORMALIZATION_LEVELS:
        raise ValueError(f"Unsupported text normalization level: {level}")
    if level == "off":
        return text

    normalized = text

    normalized = _DATE_RE.sub(
        lambda m: f"{_year_to_zh(m.group(1))}年{_number_to_zh(m.group(2))}月{_number_to_zh(m.group(3))}日",
        normalized,
    )
    normalized = _PERCENT_RE.sub(lambda m: f"百分之{_number_to_zh(m.group(1))}", normalized)
    normalized = _CHAPTER_NUM_RE.sub(lambda m: f"第{_number_to_zh(m.group(1))}{m.group(2)}", normalized)
    normalized = _TIME_RE.sub(lambda m: f"{_number_to_zh(m.group(1))}点{_number_to_zh(m.group(2))}分", normalized)
    normalized = _CJK_CONTEXT_NUM_RE.sub(lambda m: _number_to_zh(m.group(1)), normalized)

    lines = [line.strip() for line in normalized.splitlines()]
    normalized = "\n".join(line for line in lines if line)
    normalized = _MULTISPACE_RE.sub(" ", normalized)
    return normalized.strip()
