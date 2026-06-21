"""Shared utilities for charset data loading and codec iteration."""
from collections.abc import Callable
import json
import pathlib


def load_json(filename: str) -> set[int]:
    path = pathlib.Path(__file__).resolve().parent / "data" / filename
    return set(json.loads(path.read_text()))


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
