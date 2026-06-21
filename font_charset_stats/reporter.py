"""Report formatter — text (terminal table), JSON, CSV output."""

import csv
import io
import json

from font_charset_stats.analyzer import CoverageResult
from font_charset_stats.font_reader import FontInfo


def _format_text(font_info: FontInfo, results: list[CoverageResult], show_missing: bool) -> str:
    lines: list[str] = []
    lines.append(f"Font: {font_info.family_name} {font_info.style_name}")
    lines.append(f"Path: {font_info.path}")
    lines.append(
        f"Format: {font_info.format} | Glyphs: {font_info.glyph_count}"
        f" | Codepoints: {len(font_info.codepoints)}"
    )
    lines.append("")

    if not results:
        return "No results."

    name_width = max(max(len(r.name) for r in results), 15)
    total_width = 8
    matched_width = 8
    cov_width = 9

    header = (
        f"  {''.ljust(name_width)}  "
        f"{'Total'.rjust(total_width)}  "
        f"{'Matched'.rjust(matched_width)}  "
        f"{'Coverage'.rjust(cov_width)}"
    )
    sep = "-" * len(header)
    lines.append(header)
    lines.append(sep)

    for r in results:
        row = (
            f"  {r.name.ljust(name_width)}  "
            f"{str(r.total).rjust(total_width)}  "
            f"{str(r.matched).rjust(matched_width)}  "
            f"{r.coverage_pct.rjust(cov_width)}"
        )
        lines.append(row)

        if show_missing and r.missing:
            missing_preview = r.missing[:20]
            missing_hex = " ".join(f"U+{cp:04X}" for cp in missing_preview)
            suffix = " ..." if len(r.missing) > 20 else ""
            lines.append(f"    Missing ({len(r.missing)}): {missing_hex}{suffix}")

    return "\n".join(lines)


def _format_json(font_info: FontInfo, results: list[CoverageResult], show_missing: bool) -> str:
    output = {
        "font": {
            "path": str(font_info.path),
            "family_name": font_info.family_name,
            "style_name": font_info.style_name,
            "format": font_info.format,
            "glyph_count": font_info.glyph_count,
            "codepoint_count": len(font_info.codepoints),
        },
        "results": [
            {
                "name": r.name,
                "description": r.description,
                "total": r.total,
                "matched": r.matched,
                "coverage": round(r.coverage, 6),
                **(
                    {"missing": [f"U+{cp:04X}" for cp in r.missing]}
                    if show_missing and r.missing
                    else {}
                ),
            }
            for r in results
        ],
    }
    return json.dumps(output, indent=2, ensure_ascii=False)


def _format_csv(_font_info: FontInfo, results: list[CoverageResult], _show_missing: bool) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["charset", "total", "matched", "coverage"])
    for r in results:
        writer.writerow([r.name, r.total, r.matched, round(r.coverage, 6)])
    return buf.getvalue()


def format_report(
    font_info: FontInfo,
    results: list[CoverageResult],
    fmt: str = "text",
    show_missing: bool = False,
) -> str:
    formatters = {
        "text": _format_text,
        "json": _format_json,
        "csv": _format_csv,
    }
    if fmt not in formatters:
        raise ValueError(f"Unknown format: {fmt!r}. Available: {list(formatters.keys())}")
    return formatters[fmt](font_info, results, show_missing)
