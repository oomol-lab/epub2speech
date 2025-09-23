import re
from html.parser import HTMLParser

_BLOCK_ELEMENTS: tuple[str, ...] = ("p", "div", "h1", "h2", "h3", "h4", "li", "br", "hr")
_BLACKLIST_TAGS: tuple[str, ...] = ("script", "style", "noscript", "iframe", "object", "embed", "param", "source", "track", "canvas", "svg", "math", "template", "slot")

class _TextExtractor(HTMLParser):
    """HTML text extractor that extracts plain text from specific HTML elements"""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        # attrs parameter is required by HTMLParser but not used in this implementation
        _ = attrs  # Suppress unused parameter warning
        self.current_tag = tag
        # Add spacing for block elements
        if tag in _BLOCK_ELEMENTS:
            self.text_parts.append(" ")

    def handle_endtag(self, tag):
        if tag in _BLOCK_ELEMENTS[:7]:  # 排除 br, hr 自关闭标签
            self.text_parts.append(" ")
        self.current_tag = None

    def handle_data(self, data):
        if self.current_tag is None or self.current_tag.lower() not in _BLACKLIST_TAGS:
            clean_data = data.strip()
            if clean_data:
                self.text_parts.append(clean_data)

    def get_text(self) -> str:
        """Get extracted text with cleaned whitespace"""
        text = " ".join(self.text_parts)
        text = re.sub(r"\s+", " ", text).strip()
        return text


def debug_html_content(html_content: str, max_chars: int = 1000) -> None:
    """
    Debug function to print HTML content for inspection

    Args:
        html_content: HTML content to debug
        max_chars: Maximum characters to print
    """
    print("=== DEBUG HTML CONTENT ===")
    print(f"Content length: {len(html_content)} characters")
    print(f"First {max_chars} characters:")
    print(html_content[:max_chars])
    if len(html_content) > max_chars:
        print(f"... (truncated, total {len(html_content)} chars)")
    print("=== END DEBUG ===")


def extract_text_from_html(html_content: str) -> str:
    """
    Extract plain text from HTML content using HTMLParser,
    with regex fallback only for XML parsing errors

    Args:
        html_content: HTML content as string

    Returns:
        Extracted plain text

    Raises:
        Various exceptions for non-XML parsing related errors
    """
    try:
        extractor = _TextExtractor()
        extractor.feed(html_content)
        return extractor.get_text()

    except (ValueError, TypeError):
        # Only catch XML/HTML parsing specific errors
        return _extract_text_with_regex(html_content)


def _extract_text_with_regex(html_content: str) -> str:
    """
    Regex-based text extraction fallback
    Used only when HTMLParser fails due to malformed HTML

    Args:
        html_content: HTML content as string

    Returns:
        Extracted plain text
    """
    # Remove script and style content
    content = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL | re.IGNORECASE)

    # Extract text from allowed tags
    text_parts = []
    for tag in ['title', 'p', 'h1', 'h2', 'h3', 'h4', 'li', 'div']:
        pattern = f"<{tag}[^>]*>(.*?)</{tag}>"
        matches = re.findall(pattern, content, flags=re.DOTALL | re.IGNORECASE)
        for match in matches:
            clean_text = re.sub(r"<[^>]+>", "", match).strip()
            if clean_text:
                text_parts.append(clean_text)

    # Also extract any remaining text outside specific tags
    all_text = re.sub(r"<[^>]+>", " ", content)
    all_text = re.sub(r"\s+", " ", all_text).strip()
    if all_text and len(text_parts) == 0:
        text_parts.append(all_text)

    return " ".join(text_parts)