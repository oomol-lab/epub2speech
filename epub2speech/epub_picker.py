import re
import xml.etree.ElementTree as ET

from os import PathLike
from typing import Any, Generator, Literal
from ebooklib import epub, ITEM_COVER, ITEM_IMAGE, ITEM_NAVIGATION
from .extractor import extract_text_from_html


class EpubPicker:
    def __init__(self, file_path: PathLike) -> None:
        self._book: epub.EpubBook = epub.read_epub(file_path)
        nav_item, epub_version = self._determine_epub_type()
        self._nav_item: Any = nav_item
        self._epub_version: Literal["EPUB2", "EPUB3"] | None = epub_version

    def _determine_epub_type(self) -> tuple[Any | None, Literal["EPUB2", "EPUB3"] | None]:
        for item in self._book.get_items_of_type(ITEM_NAVIGATION):
            if item and item.file_name and item.file_name.endswith('.ncx'):
                return (item, "EPUB2")

        for item in self._book.get_items():
            if item and item.file_name and item.file_name.endswith('.xhtml'):
                content = item.get_content()
                if content:
                    if isinstance(content, bytes):
                        content = content.decode("utf-8", errors="ignore")
                    if 'epub:type="toc"' in content or "epub:type='toc'" in content:
                        return (item, "EPUB3")
        return (None, None)

    @property
    def epub_version(self) -> Literal["EPUB2", "EPUB3"] | None:
        return self._epub_version

    @property
    def cover_bytes(self) -> bytes | None:
        cover_item = self._find_cover_item(self._book)
        if cover_item is not None:
            content = cover_item.get_content()
            if isinstance(content, bytes):
                return content
        return None

    def _find_cover_item(self, book: epub.EpubBook):
        def is_image(item: Any):
            return item is not None and item.media_type.startswith("image/")

        for item in book.get_items_of_type(ITEM_COVER):
            if is_image(item):
                return item

        # https://idpf.org/forum/topic-715
        for meta in book.get_metadata("OPF", "cover"):
            if is_image(item := book.get_item_with_id(meta[1]["content"])):
                return item

        if is_image(item := book.get_item_with_id("cover")):
            return item

        for item in book.get_items_of_type(ITEM_IMAGE):
            if "cover" in item.get_name().lower() and is_image(item):
                return item

        return None

    @property
    def title(self) -> list[str]:
        return self._get_metadata_names("title")

    @property
    def author(self) -> list[str]:
        return self._get_metadata_names("creator")

    def _get_metadata_names(self, meta_name: str) -> list[str]:
        metadatas = self._book.get_metadata("DC", meta_name)
        return [str(meta[0]) for meta in metadatas if meta and meta[0]]

    def get_nav_items(self) -> Generator[tuple[str, str], None, None]:
        if self._epub_version is not None:
            content = self._nav_item.get_content()
            if content is None:
                return
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")
            if self._epub_version == "EPUB2":
                yield from self._parse_epub2_ncx(content)
            elif self._epub_version == "EPUB3":
                yield from self._parse_epub3_nav(content)
        else:
            yield from self._generate_virtual_navigation()

    def extract_text(self, href: str) -> str:
        base_href = href.split('#')[0] if '#' in href else href

        doc_item = self._book.get_item_with_href(base_href)

        if doc_item is None:
            doc_item = self._book.get_item_with_href(href)

        if doc_item is None:
            return ""

        content = doc_item.get_content()
        if content is None:
            return ""

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")

        return extract_text_from_html(content)

    def _parse_epub2_ncx(self, content: str) -> Generator[tuple[str, str], None, None]:
        root = ET.fromstring(content)
        ns = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}
        nav_points = root.findall(".//ncx:navPoint", ns) or root.findall(".//navPoint")

        for nav_point in nav_points:
            nav_label = nav_point.find("ncx:navLabel", ns)
            if nav_label is None:
                nav_label = nav_point.find("navLabel")

            content_elem = nav_point.find("ncx:content", ns)
            if content_elem is None:
                content_elem = nav_point.find("content")

            if nav_label is not None and content_elem is not None:
                text_elem = nav_label.find("ncx:text", ns)
                if text_elem is None:
                    text_elem = nav_label.find("text")

                title = text_elem.text if text_elem is not None else ""
                href = content_elem.get("src", "")

                if title and href:
                    yield (title.strip(), href)

    def _parse_epub3_nav(self, content: str) -> Generator[tuple[str, str], None, None]:
        root = ET.fromstring(content)
        nav_elements = root.findall(".//nav") or root.findall(".//{http://www.w3.org/1999/xhtml}nav")
        found_nav_toc = False
        for nav_elem in nav_elements:
            nav_type = nav_elem.get("epub:type") or nav_elem.get("{http://www.idpf.org/2007/ops}type")
            if nav_type == "toc":
                found_nav_toc = True
                yield from self._extract_links_from_element(nav_elem)
                break

        if not found_nav_toc:
            if nav_elements:
                yield from self._extract_links_from_element(nav_elements[0])
            else:
                yield from self._extract_links_from_element(root)

    def _extract_links_from_element(self, element: ET.Element) -> Generator[tuple[str, str], None, None]:
        links = element.findall(".//a") or element.findall(".//{http://www.w3.org/1999/xhtml}a")
        for link in links:
            href = link.get("href")
            if href:
                title = "".join(link.itertext()).strip()
                if title:
                    yield (title, href)

    def _generate_virtual_navigation(self) -> Generator[tuple[str, str], None, None]:
        documents = []
        for item in self._book.get_items():
            if item and item.file_name:
                media_type = getattr(item, "media_type", "")
                if media_type in ["application/xhtml+xml", "text/html"] or item.file_name.endswith('.xhtml'):
                    documents.append(item)

        documents.sort(key=lambda x: x.file_name if x.file_name else '')

        if not documents:
            titles = self._book.get_metadata("DC", "title")
            title = str(titles[0]) if titles and titles[0] else "Content"
            yield (title, "content.xhtml")
            return

        if len(documents) == 1:
            doc = documents[0]
            title = self._extract_title_from_filename(doc.file_name) or "Content"
            yield (title, doc.file_name)
            return

        for i, doc in enumerate(documents, 1):
            title = self._extract_title_from_filename(doc.file_name) or f"Page {i}"
            yield (title, doc.file_name)

    def _extract_title_from_filename(self, filename: str) -> str:
        if not filename:
            return ""

        from pathlib import Path
        stem = Path(filename).stem

        title = stem.replace("_", " ").replace("-", " ")

        title = re.sub(r'\b(chapter|section|part|page)\s*(\d+)\b', r'\1 \2', title, flags=re.IGNORECASE)
        title = re.sub(r'\b(\d+)\s*(chapter|section|part|page)\b', r'\2 \1', title, flags=re.IGNORECASE)

        return title.title() if title else ""