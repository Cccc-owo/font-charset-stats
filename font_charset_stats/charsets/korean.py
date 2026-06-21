"""Korean character sets: Hangul, Jamo, and KS X 1001 Hanja."""

from font_charset_stats.charsets import register
from font_charset_stats.charsets._utils import load_json, range_builder
from font_charset_stats.charsets.base import CharSet

register(
    CharSet(
        name="Korean-Hangul",
        description="Hangul Syllables (U+AC00–U+D7AF, 11,172 precomposed syllables)",
        builder=range_builder(0xAC00, 0xD7AF),
    )
)

register(
    CharSet(
        name="Korean-Jamo",
        description="Hangul Jamo (U+1100–U+11FF) + Compatibility Jamo (U+3130–U+318F)",
        builder=lambda: set(range(0x1100, 0x11FF + 1)) | set(range(0x3130, 0x318F + 1)),
    )
)

register(
    CharSet(
        name="KSX1001-Hanja",
        description="KS X 1001 Hanja — Korean Chinese characters (4,620 hanja)",
        builder=lambda: load_json("ksx1001_hanja.json"),
    )
)
