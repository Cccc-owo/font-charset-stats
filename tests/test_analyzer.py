from font_charset_stats.analyzer import CoverageResult, analyze
from font_charset_stats.charsets.base import CharSet


def _make_cs(name: str, cps: set[int]) -> CharSet:
    return CharSet(name=name, description=f"Test {name}", builder=lambda: cps)


class TestCoverageResult:
    def test_coverage_full(self):
        r = CoverageResult(name="test", description="", total=10, matched=10)
        assert r.coverage == 1.0
        assert r.coverage_pct == "100.00%"

    def test_coverage_partial(self):
        r = CoverageResult(name="test", description="", total=10, matched=3)
        assert r.coverage == 0.3
        assert r.coverage_pct == "30.00%"

    def test_coverage_zero_total(self):
        r = CoverageResult(name="test", description="", total=0, matched=0)
        assert r.coverage == 1.0

    def test_missing(self):
        r = CoverageResult(name="test", description="", total=5, matched=2, missing=[3, 4, 5])
        assert r.missing == [3, 4, 5]


class TestAnalyze:
    def test_empty_font(self):
        cs = _make_cs("Latin", {65, 66, 67})
        results = analyze(set(), [cs])
        assert len(results) == 1
        assert results[0].matched == 0

    def test_full_match(self):
        cs = _make_cs("test", {65, 66, 67})
        results = analyze({65, 66, 67}, [cs])
        assert results[0].matched == 3
        assert results[0].coverage == 1.0

    def test_partial_match(self):
        cs = _make_cs("test", {65, 66, 67, 68})
        results = analyze({65, 66}, [cs])
        assert results[0].matched == 2
        assert results[0].coverage == 0.5

    def test_show_missing(self):
        cs = _make_cs("test", {65, 66, 67})
        results = analyze({65}, [cs], show_missing=True)
        assert results[0].missing == [66, 67]

    def test_no_show_missing(self):
        cs = _make_cs("test", {65, 66, 67})
        results = analyze({65}, [cs], show_missing=False)
        assert results[0].missing == []

    def test_exclude_controls(self):
        cs = _make_cs("test", {65, 0x01, 0x7F, 66})
        results = analyze({65, 66, 0x01}, [cs], exclude_controls=True)
        assert results[0].total == 2
        assert results[0].matched == 2

    def test_exclude_controls_keeps_when_false(self):
        cs = _make_cs("test", {65, 0x01})
        results = analyze({65, 0x01}, [cs], exclude_controls=False)
        assert results[0].total == 2
        assert results[0].matched == 2

    def test_multiple_charsets(self):
        cs1 = _make_cs("A", {65, 66})
        cs2 = _make_cs("B", {66, 67})
        results = analyze({65, 66}, [cs1, cs2])
        assert results[0].name == "A"
        assert results[0].matched == 2
        assert results[1].name == "B"
        assert results[1].matched == 1

    def test_non_char_range_control(self):
        cs = _make_cs("test", {0x00, 0x1F, 0x7F, 0x9F, 65})
        results = analyze({65, 0x00}, [cs], exclude_controls=True)
        assert results[0].total == 1
        assert results[0].matched == 1
