"""Font file reader — extracts Unicode codepoint coverage via fonttools."""
from dataclasses import dataclass, field
from pathlib import Path

from fontTools.ttLib import TTFont


@dataclass
class FontInfo:
    path: Path
    format: str  # e.g. "truetype", "opentype", "woff"
    family_name: str = ""
    style_name: str = ""
    glyph_count: int = 0
    codepoints: set[int] = field(default_factory=set)


def _deduce_format(font: TTFont) -> str:
    flavor = getattr(font, "flavor", None)
    if flavor == "woff2":
        return "woff2"
    if flavor == "woff":
        return "woff"
    if "CFF " in font.keys() or "CFF2" in font.keys():
        return "opentype"
    return "truetype"


def read_font(font_path: str | Path) -> FontInfo:
    path = Path(font_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Font file not found: {path}")

    font = TTFont(path, fontNumber=0)
    try:
        fmt = _deduce_format(font)

        family_name = ""
        style_name = ""
        name_table = font.get("name")
        if name_table:
            for record in name_table.names:
                try:
                    text = record.toUnicode()
                except (UnicodeDecodeError, AttributeError):
                    continue
                if record.nameID == 1:
                    family_name = text
                elif record.nameID == 2:
                    style_name = text

        glyph_count = 0
        maxp_table = font.get("maxp")
        if maxp_table:
            glyph_count = getattr(maxp_table, "numGlyphs", 0)

        cmap = font.getBestCmap()
        codepoints: set[int] = set()
        if cmap:
            codepoints = set(cmap.keys())

        return FontInfo(
            path=path,
            format=fmt,
            family_name=family_name,
            style_name=style_name,
            glyph_count=glyph_count,
            codepoints=codepoints,
        )
    finally:
        font.close()
