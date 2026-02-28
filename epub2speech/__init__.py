from __future__ import annotations

from typing import TYPE_CHECKING, Any

from . import tts

if TYPE_CHECKING:
    from .convertor import ConversionProgress, convert_epub_to_m4b

__all__ = [
    "tts",
    "convert_epub_to_m4b",
    "ConversionProgress",
]


def __getattr__(name: str) -> Any:
    if name in {"convert_epub_to_m4b", "ConversionProgress"}:
        from .convertor import ConversionProgress, convert_epub_to_m4b

        exports: dict[str, Any] = {
            "convert_epub_to_m4b": convert_epub_to_m4b,
            "ConversionProgress": ConversionProgress,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
