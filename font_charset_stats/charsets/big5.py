"""Big5 and Big5-HKSCS traditional Chinese encoding standards."""

import codecs

from font_charset_stats.charsets import register
from font_charset_stats.charsets._utils import try_decode
from font_charset_stats.charsets.base import CharSet


def _build_big5() -> set[int]:
    decoder = codecs.getdecoder("big5")
    result: set[int] = set()
    for b1 in range(0xA1, 0xFE):
        for b2 in range(0x40, 0x7F):
            try_decode(decoder, bytes([b1, b2]), result)
        for b2 in range(0xA1, 0xFF):
            try_decode(decoder, bytes([b1, b2]), result)
    return result


def _build_big5hkscs() -> set[int]:
    decoder = codecs.getdecoder("big5hkscs")
    result: set[int] = set()
    for b1 in range(0x81, 0xFF):
        for b2 in range(0x40, 0x7F):
            try_decode(decoder, bytes([b1, b2]), result)
        for b2 in range(0xA1, 0xFF):
            try_decode(decoder, bytes([b1, b2]), result)
    return result


register(
    CharSet(
        name="Big5",
        description="Big5 — Traditional Chinese encoding (Taiwan, ~13,000 characters)",
        builder=_build_big5,
    )
)

register(
    CharSet(
        name="Big5-HKSCS",
        description="Big5-HKSCS — Big5 + Hong Kong Supplementary Character Set (~18,000 characters)",
        builder=_build_big5hkscs,
    )
)
