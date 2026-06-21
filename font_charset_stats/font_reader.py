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
    font_number: int = 0


def probe_tc(path: str | Path) -> list[tuple[int, str, str, int]]:
    """Return list of (font_number, family_name, style_name, weight_class)
    for each face in a TTC/OTC."""
    path = Path(path)
    if not path.exists():
        return []
    try:
        font = TTFont(path, fontNumber=0)
        try:
            reader = getattr(font, "reader", None)
            count = reader.numFonts if reader and hasattr(reader, "numFonts") else 1
        finally:
            font.close()
        if count <= 1:
            return []

        variants: list[tuple[int, str, str, int]] = []
        for i in range(count):
            f = None
            try:
                f = TTFont(path, fontNumber=i)
                family = ""
                style = ""
                weight = 400
                name_table = f.get("name")
                if name_table:
                    for record in name_table.names:
                        try:
                            text = record.toUnicode()
                        except (UnicodeDecodeError, AttributeError):
                            continue
                        if record.nameID == 1 and not family:
                            family = text
                        elif record.nameID == 2 and not style:
                            style = text
                os2 = f.get("OS/2")
                if os2:
                    weight = getattr(os2, "usWeightClass", 400)
                glyphs = getattr(f.get("maxp"), "numGlyphs", 0) if f.get("maxp") else 0
                variants.append((i, family or f"Face {i}", style or f"{glyphs} glyphs", weight))
            except Exception:
                variants.append((i, f"Face {i}", "?", 400))
            finally:
                if f is not None:
                    f.close()
        return variants
    except Exception:
        return []


def _deduce_format(font: TTFont) -> str:
    flavor = getattr(font, "flavor", None)
    if flavor == "woff2":
        return "woff2"
    if flavor == "woff":
        return "woff"
    if "CFF " in font or "CFF2" in font:
        return "opentype"
    if "GSUB" in font or "GPOS" in font:
        return "opentype"
    return "truetype"


def read_font(font_path: str | Path, font_number: int = 0) -> FontInfo:
    path = Path(font_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Font file not found: {path}")

    font = TTFont(path, fontNumber=font_number)
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
            font_number=font_number,
        )
    finally:
        font.close()
