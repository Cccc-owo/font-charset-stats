from font_charset_stats.analyzer import CoverageResult, analyze
from font_charset_stats.charsets import ALL_CHARSETS, get_charset, list_charsets
from font_charset_stats.font_reader import FontInfo, read_font
from font_charset_stats.reporter import format_report


def analyze_font(
    font_path: str,
    charsets: list[str] | None = None,
    fmt: str = "text",
    show_missing: bool = False,
) -> str:
    """Convenience function: read font, analyze all/specified charsets, return formatted report."""
    font_info = read_font(font_path)

    if charsets:
        cs_list = [get_charset(n) for n in charsets]
    else:
        cs_list = [ALL_CHARSETS[n] for n in list_charsets()]

    results = analyze(font_info.codepoints, cs_list, show_missing=show_missing)
    return format_report(font_info, results, fmt=fmt, show_missing=show_missing)


__all__ = [
    "analyze",
    "analyze_font",
    "CoverageResult",
    "read_font",
    "FontInfo",
    "format_report",
    "get_charset",
    "list_charsets",
    "ALL_CHARSETS",
]
