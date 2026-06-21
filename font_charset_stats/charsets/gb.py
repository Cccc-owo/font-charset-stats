"""GB encoding standards: GB2312, GBK, GB18030-2022 Level 1/2/3."""

import codecs

from font_charset_stats.charsets import register
from font_charset_stats.charsets._utils import load_json, load_or_build, try_decode
from font_charset_stats.charsets.base import CharSet


def _build_gb2312() -> set[int]:
    decoder = codecs.getdecoder("gb2312")
    result: set[int] = set()
    for b1 in range(0xA1, 0xFF):
        for b2 in range(0xA1, 0xFF):
            try_decode(decoder, bytes([b1, b2]), result)
    return result


def _build_gbk() -> set[int]:
    decoder = codecs.getdecoder("gbk")
    result: set[int] = set()
    for b1 in range(0x81, 0xFF):
        for b2 in range(0x40, 0x7F):
            try_decode(decoder, bytes([b1, b2]), result)
        for b2 in range(0x80, 0xFF):
            try_decode(decoder, bytes([b1, b2]), result)
    return result


register(
    CharSet(
        name="GB2312",
        description="GB/T 2312-1980 — Simplified Chinese national standard (7,445 characters)",
        builder=load_or_build("gb2312.json", _build_gb2312),
    )
)

register(
    CharSet(
        name="GBK",
        description="GBK — Extended Simplified Chinese, superset of GB2312 (~21,886 characters)",
        builder=load_or_build("gbk.json", _build_gbk),
    )
)

register(
    CharSet(
        name="GB18030-Level1",
        description="GB 18030-2022 Implementation Level 1 (mandatory) — GBK + Ext A + 66 URO additions (~27,584)",
        builder=lambda: load_json("gb18030_level1.json"),
    )
)

register(
    CharSet(
        name="GB18030-Level2",
        description="GB 18030-2022 Implementation Level 2 — Level 1 + 196 TGH 2013 ideographs from Ext B/C/D/E",
        builder=lambda: load_json("gb18030_level2.json"),
    )
)

register(
    CharSet(
        name="GB18030-Level3",
        description="GB 18030-2022 Implementation Level 3 (full) — all encodable characters incl. Ext B-F, Kangxi, minority scripts",
        builder=lambda: load_json("gb18030_level3.json"),
    )
)
