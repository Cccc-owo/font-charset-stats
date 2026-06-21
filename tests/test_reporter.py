import json
from pathlib import Path

import pytest

from font_charset_stats.analyzer import CoverageResult
from font_charset_stats.font_reader import FontInfo
from font_charset_stats.reporter import format_report


def _make_fi() -> FontInfo:
    return FontInfo(
        path=Path("test/TestFont-Regular.ttf"),
        format="truetype",
        family_name="Test Font",
        style_name="Regular",
        glyph_count=100,
        codepoints={65, 66, 67},
    )


def _make_results() -> list[CoverageResult]:
    return [
        CoverageResult(name="Latin", description="Basic Latin", total=128, matched=65, missing=[]),
        CoverageResult(
            name="CJK",
            description="CJK Unified",
            total=20992,
            matched=1000,
            missing=[0x4E01, 0x4E02, 0x4E03, 0x4E04, 0x4E05],
        ),
    ]


class TestFormatReport:
    def test_text_format(self):
        fi = _make_fi()
        results = _make_results()
        output = format_report(fi, results, fmt="text")
        assert "Test Font" in output
        assert "Latin" in output
        assert "CJK" in output
        assert "128" in output

    def test_json_format(self):
        fi = _make_fi()
        results = _make_results()
        output = format_report(fi, results, fmt="json")
        data = json.loads(output)
        assert data["font"]["family_name"] == "Test Font"
        assert len(data["results"]) == 2
        assert data["results"][0]["name"] == "Latin"

    def test_csv_format(self):
        fi = _make_fi()
        results = _make_results()
        output = format_report(fi, results, fmt="csv")
        lines = output.strip().split("\n")
        assert lines[0].strip() == "charset,total,matched,coverage"
        assert lines[1].startswith("Latin")

    def test_text_with_missing(self):
        fi = _make_fi()
        results = _make_results()
        output = format_report(fi, results, fmt="text", show_missing=True)
        assert "Missing" in output
        assert "U+4E01" in output

    def test_json_with_missing(self):
        fi = _make_fi()
        results = _make_results()
        output = format_report(fi, results, fmt="json", show_missing=True)
        data = json.loads(output)
        assert "missing" in data["results"][1]
        assert len(data["results"][1]["missing"]) == 5

    def test_invalid_format(self):
        fi = _make_fi()
        results = _make_results()
        with pytest.raises(ValueError, match="Unknown format"):
            format_report(fi, results, fmt="xml")

    def test_empty_results_text(self):
        fi = _make_fi()
        output = format_report(fi, [], fmt="text")
        assert "No results" in output
