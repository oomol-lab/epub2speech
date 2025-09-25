import re
from html.parser import HTMLParser

_BLOCK_ELEMENTS: tuple[str, ...] = ("p", "div", "h1", "h2", "h3", "h4", "li", "br", "hr")
_BLACKLIST_TAGS: tuple[str, ...] = ("script", "style", "noscript", "iframe", "object", "embed", "param", "source", "track", "canvas", "svg", "math", "template", "slot")

class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        _ = attrs
        self.current_tag = tag
        if tag in _BLOCK_ELEMENTS:
            self.text_parts.append(" ")

    def handle_endtag(self, tag):
        if tag in _BLOCK_ELEMENTS[:7]:
            self.text_parts.append(" ")
        self.current_tag = None

    def handle_data(self, data):
        if self.current_tag is None or self.current_tag.lower() not in _BLACKLIST_TAGS:
            clean_data = data.strip()
            if clean_data:
                self.text_parts.append(clean_data)

    def get_text(self) -> str:
        text = " ".join(self.text_parts)
        text = re.sub(r"\s+", " ", text).strip()
        return text


def debug_html_content(html_content: str, max_chars: int = 1000) -> None:
    print("=== DEBUG HTML CONTENT ===")
    print(f"Content length: {len(html_content)} characters")
    print(f"First {max_chars} characters:")
    print(html_content[:max_chars])
    if len(html_content) > max_chars:
        print(f"... (truncated, total {len(html_content)} chars)")
    print("=== END DEBUG ===")


def extract_text_from_html(html_content: str) -> str:
    try:
        extractor = _TextExtractor()
        extractor.feed(html_content)
        return extractor.get_text()

    except (ValueError, TypeError):
        return _extract_text_with_regex(html_content)


def _extract_text_with_regex(html_content: str) -> str:
    content = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL | re.IGNORECASE)

    text_parts = []
    for tag in ["title", "p", "h1", "h2", "h3", "h4", "li", "div"]:
        pattern = f"<{tag}[^>]*>(.*?)</{tag}>"
        matches = re.findall(pattern, content, flags=re.DOTALL | re.IGNORECASE)
        for match in matches:
            clean_text = re.sub(r"<[^>]+>", "", match).strip()
            if clean_text:
                text_parts.append(clean_text)

    all_text = re.sub(r"<[^>]+>", " ", content)
    all_text = re.sub(r"\s+", " ", all_text).strip()
    if all_text and len(text_parts) == 0:
        text_parts.append(all_text)

    return " ".join(text_parts)