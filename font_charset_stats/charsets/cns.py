"""CNS 11643 — Taiwan national standard for Chinese characters."""

from font_charset_stats.charsets import register
from font_charset_stats.charsets._utils import load_json
from font_charset_stats.charsets.base import CharSet

register(
    CharSet(
        name="CNS11643",
        description="CNS 11643 — Taiwan national standard, 16 planes (~17,711 characters)",
        builder=lambda: load_json("cns11643.json"),
    )
)
