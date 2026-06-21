"""Unicode blocks — Latin, Greek, Cyrillic, punctuation, and symbol ranges."""

from font_charset_stats.charsets import register
from font_charset_stats.charsets._utils import range_builder
from font_charset_stats.charsets.base import CharSet

_BLOCKS: list[tuple[str, str, int, int]] = [
    # ── Latin ────────────────────────────────────────────
    ("Basic Latin", "Basic Latin (U+0000–U+007F)", 0x0000, 0x007F),
    ("Latin-1 Supplement", "Latin-1 Supplement (U+0080–U+00FF)", 0x0080, 0x00FF),
    ("Latin Extended-A", "Latin Extended-A (U+0100–U+017F)", 0x0100, 0x017F),
    ("Latin Extended-B", "Latin Extended-B (U+0180–U+024F)", 0x0180, 0x024F),
    ("IPA Extensions", "IPA Extensions (U+0250–U+02AF)", 0x0250, 0x02AF),
    ("Spacing Modifier", "Spacing Modifier Letters (U+02B0–U+02FF)", 0x02B0, 0x02FF),
    (
        "Combining Diacritical",
        "Combining Diacritical Marks (U+0300–U+036F)",
        0x0300,
        0x036F,
    ),
    # ── Greek / Cyrillic ─────────────────────────────────
    ("Greek and Coptic", "Greek and Coptic (U+0370–U+03FF)", 0x0370, 0x03FF),
    ("Cyrillic", "Cyrillic (U+0400–U+04FF)", 0x0400, 0x04FF),
    ("Cyrillic Supplement", "Cyrillic Supplement (U+0500–U+052F)", 0x0500, 0x052F),
    # ── Punctuation ══════════════════════════════════════
    ("General Punctuation", "General Punctuation (U+2000–U+206F)", 0x2000, 0x206F),
    (
        "Superscript/Subscript",
        "Superscripts & Subscripts (U+2070–U+209F)",
        0x2070,
        0x209F,
    ),
    ("Currency Symbols", "Currency Symbols (U+20A0–U+20CF)", 0x20A0, 0x20CF),
    ("Letterlike Symbols", "Letterlike Symbols (U+2100–U+214F)", 0x2100, 0x214F),
    ("Number Forms", "Number Forms (U+2150–U+218F)", 0x2150, 0x218F),
    ("Arrows", "Arrows (U+2190–U+21FF)", 0x2190, 0x21FF),
    (
        "Mathematical Operators",
        "Mathematical Operators (U+2200–U+22FF)",
        0x2200,
        0x22FF,
    ),
    # ── Drawing / Shapes ─────────────────────────────────
    ("Box Drawing", "Box Drawing (U+2500–U+257F)", 0x2500, 0x257F),
    ("Block Elements", "Block Elements (U+2580–U+259F)", 0x2580, 0x259F),
    ("Geometric Shapes", "Geometric Shapes (U+25A0–U+25FF)", 0x25A0, 0x25FF),
    ("Miscellaneous Symbols", "Miscellaneous Symbols (U+2600–U+26FF)", 0x2600, 0x26FF),
    ("Dingbats", "Dingbats (U+2700–U+27BF)", 0x2700, 0x27BF),
]

for name, desc, start, end in _BLOCKS:
    register(CharSet(name=name, description=desc, builder=range_builder(start, end)))
