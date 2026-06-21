"""Unicode CJK Unified Ideograph ranges."""
from font_charset_stats.charsets import register
from font_charset_stats.charsets._utils import range_builder
from font_charset_stats.charsets.base import CharSet

CJK_BLOCKS: list[tuple[str, str, int, int]] = [
    ("CJK-Basic", "CJK Unified Ideographs (U+4E00–U+9FFF)", 0x4E00, 0x9FFF),
    ("CJK-ExtA", "CJK Extension A (U+3400–U+4DBF)", 0x3400, 0x4DBF),
    ("CJK-ExtB", "CJK Extension B (U+20000–U+2A6DF)", 0x20000, 0x2A6DF),
    ("CJK-ExtC", "CJK Extension C (U+2A700–U+2B73F)", 0x2A700, 0x2B73F),
    ("CJK-ExtD", "CJK Extension D (U+2B740–U+2B81F)", 0x2B740, 0x2B81F),
    ("CJK-ExtE", "CJK Extension E (U+2B820–U+2CEAF)", 0x2B820, 0x2CEAF),
    ("CJK-ExtF", "CJK Extension F (U+2CEB0–U+2EBEF)", 0x2CEB0, 0x2EBEF),
    ("CJK-ExtG", "CJK Extension G (U+30000–U+3134F)", 0x30000, 0x3134F),
    ("CJK-ExtH", "CJK Extension H (U+31350–U+323AF)", 0x31350, 0x323AF),
    ("CJK-ExtI", "CJK Extension I (U+2EBF0–U+2EE5F)", 0x2EBF0, 0x2EE5F),
    ("CJK-Compat", "CJK Compatibility Ideographs (U+F900–U+FAFF)", 0xF900, 0xFAFF),
    ("CJK-CompatSup", "CJK Compatibility Supplement (U+2F800–U+2FA1F)", 0x2F800, 0x2FA1F),
]

for name, desc, start, end in CJK_BLOCKS:
    register(CharSet(name=name, description=desc, builder=range_builder(start, end)))
