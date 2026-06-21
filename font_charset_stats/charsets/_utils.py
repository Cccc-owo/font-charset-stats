"""Shared utilities for charset data loading and codec iteration."""

import json
import pathlib
import unicodedata
from collections.abc import Callable


def load_json(filename: str) -> set[int]:
    path = pathlib.Path(__file__).resolve().parent / "data" / filename
    return set(json.loads(path.read_text()))


def load_or_build(filename: str, builder: Callable[[], set[int]]) -> Callable[[], set[int]]:
    def build() -> set[int]:
        data_dir = pathlib.Path(__file__).resolve().parent / "data"
        cache_path = data_dir / filename
        if cache_path.exists():
            return set(json.loads(cache_path.read_text()))
        result = builder()
        try:
            cache_path.write_text(json.dumps(sorted(result), ensure_ascii=False))
            import logging

            logging.getLogger(__name__).debug("Generated cache: %s", cache_path)
        except OSError:
            pass
        return result

    return build


def try_decode(decoder: Callable[[bytes], tuple[str, int]], seq: bytes, result: set[int]) -> None:
    try:
        chars, _ = decoder(seq)
        result.update(ord(c) for c in chars)
    except (UnicodeDecodeError, UnicodeError):
        pass


def range_builder(start: int, end: int):
    def build() -> set[int]:
        return set(range(start, end + 1))

    return build


def format_codepoint_char(cp: int) -> str:
    if 0xD800 <= cp <= 0xDFFF:
        return "(surrogate)"
    if 0xFDD0 <= cp <= 0xFDEF or cp & 0xFFFE == 0xFFFE:
        return "(nonchar)"
    if cp <= 0x1F or (0x7F <= cp <= 0x9F):
        return "(control)"
    try:
        ch = chr(cp)
        cat = unicodedata.category(ch)
        if cat.startswith("C"):
            return "(control)"
        return ch
    except (ValueError, OverflowError):
        return ""
