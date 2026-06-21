"""JIS X 0208 / JIS X 0213 Japanese encoding standards."""

import codecs

from font_charset_stats.charsets import register
from font_charset_stats.charsets._utils import load_json, load_or_build, try_decode
from font_charset_stats.charsets.base import CharSet


def _build_jisx0213() -> set[int]:
    decoder = codecs.getdecoder("euc_jis_2004")
    result: set[int] = set()
    for b1 in range(0xA1, 0xFF):
        for b2 in range(0xA1, 0xFF):
            try_decode(decoder, bytes([b1, b2]), result)
    for b1 in range(0xA1, 0xFF):
        for b2 in range(0xA1, 0xFF):
            try_decode(decoder, bytes([0x8F, b1, b2]), result)
    return result


register(
    CharSet(
        name="JIS0208-Level1",
        description="JIS X 0208 Level 1 — Common-use Japanese kanji (2,965 characters)",
        builder=lambda: load_json("jis0208_level1.json"),
    )
)

register(
    CharSet(
        name="JIS0208-Level2",
        description="JIS X 0208 Level 2 — Secondary Japanese kanji (3,390 characters)",
        builder=lambda: load_json("jis0208_level2.json"),
    )
)

register(
    CharSet(
        name="JIS0213",
        description="JIS X 0213 (EUC-JIS-2004) — Extended Japanese standard incl. JIS X 0208 + Plane 1 & 2 additions",
        builder=load_or_build("jis0213.json", _build_jisx0213),
    )
)
