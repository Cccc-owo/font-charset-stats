"""GB/T 12345-1990 — Traditional Chinese counterpart of GB2312."""
from font_charset_stats.charsets import register
from font_charset_stats.charsets._utils import load_json
from font_charset_stats.charsets.base import CharSet

register(CharSet(
    name="GB12345",
    description="GB/T 12345-1990 — Traditional Chinese national standard, GB2312 counterpart (~6,866 Hanzi)",
    builder=lambda: load_json("gb12345.json"),
))
