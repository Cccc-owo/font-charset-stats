import pytest

from font_charset_stats.charsets import ALL_CHARSETS, get_charset, list_charsets, register
from font_charset_stats.charsets._utils import format_codepoint_char, range_builder
from font_charset_stats.charsets.base import CharSet


class TestRegistration:
    def test_get_unknown_raises(self):
        with pytest.raises(KeyError, match="Unknown charset"):
            get_charset("__nonexistent_charset__")

    def test_list_charsets_returns_all(self):
        names = list_charsets()
        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)

    def test_all_charsets_contains_expected(self):
        assert "Basic Latin" in ALL_CHARSETS
        assert "GB2312" in ALL_CHARSETS
        assert "Big5" in ALL_CHARSETS
        assert "JIS0208-Level1" in ALL_CHARSETS
        assert "CJK-Basic" in ALL_CHARSETS

    def test_register_adds_to_registry(self):
        cs = CharSet(
            name="__test_register__",
            description="Test charset for registration",
            builder=lambda: {1, 2, 3},
        )
        register(cs)
        assert get_charset("__test_register__") is cs
        assert "__test_register__" in list_charsets()


class TestCharSet:
    def test_lazy_loading(self):
        calls = []

        def builder():
            calls.append(1)
            return {1, 2, 3}

        cs = CharSet(name="lazy", description="", builder=builder)
        assert len(calls) == 0
        cps = cs.codepoints
        assert cps == {1, 2, 3}
        assert len(calls) == 1
        _again = cs.codepoints
        assert len(calls) == 1

    def test_total(self):
        cs = CharSet(name="test", description="", builder=lambda: {1, 2, 3})
        assert cs.total == 3

    def test_repr(self):
        cs = CharSet(name="test", description="", builder=lambda: {1, 2, 3})
        r = repr(cs)
        assert "test" in r
        assert "total=3" in r


class TestJsonData:
    def test_gb2312_codepoints(self):
        cs = get_charset("GB2312")
        assert cs.total == 7445

    def test_gbk_codepoints(self):
        cs = get_charset("GBK")
        assert cs.total == 21791

    def test_big5_codepoints(self):
        cs = get_charset("Big5")
        assert cs.total == 13706

    def test_big5hkscs_codepoints(self):
        cs = get_charset("Big5-HKSCS")
        assert cs.total == 18388

    def test_jis0213_codepoints(self):
        cs = get_charset("JIS0213")
        assert cs.total == 14368

    def test_basic_latin(self):
        cs = get_charset("Basic Latin")
        assert cs.total == 128

    def test_cjk_basic_range(self):
        cs = get_charset("CJK-Basic")
        assert cs.total == 20992


class TestRangeBuilder:
    def test_single_value(self):
        b = range_builder(65, 65)
        assert b() == {65}

    def test_range(self):
        b = range_builder(65, 67)
        assert b() == {65, 66, 67}


class TestFormatCodepoint:
    def test_surrogate(self):
        assert format_codepoint_char(0xD800) == "(surrogate)"
        assert format_codepoint_char(0xDFFF) == "(surrogate)"

    def test_nonchar(self):
        assert format_codepoint_char(0xFDD0) == "(nonchar)"
        assert format_codepoint_char(0xFFFE) == "(nonchar)"

    def test_control(self):
        assert format_codepoint_char(0x00) == "(control)"
        assert format_codepoint_char(0x1F) == "(control)"
        assert format_codepoint_char(0x7F) == "(control)"
        assert format_codepoint_char(0x9F) == "(control)"

    def test_printable(self):
        assert format_codepoint_char(65) == "A"
        assert format_codepoint_char(0x4E00) == "\u4e00"
