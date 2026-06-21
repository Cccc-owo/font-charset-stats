"""Japanese character sets: Kana blocks."""
from font_charset_stats.charsets import register
from font_charset_stats.charsets._utils import range_builder
from font_charset_stats.charsets.base import CharSet

register(CharSet(
    name="Japanese-Hiragana",
    description="Hiragana (U+3040–U+309F)",
    builder=range_builder(0x3040, 0x309F),
))

register(CharSet(
    name="Japanese-Katakana",
    description="Katakana (U+30A0–U+30FF) + Halfwidth (U+FF65–U+FF9F) + Phonetic Ext (U+31F0–U+31FF)",
    builder=lambda: (
        set(range(0x30A0, 0x30FF + 1))
        | set(range(0xFF65, 0xFF9F + 1))
        | set(range(0x31F0, 0x31FF + 1))
    ),
))
