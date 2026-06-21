import pytest

from font_charset_stats.font_reader import FontInfo, _deduce_format, read_font
from tests.conftest import BUNDLED_FONT


class TestFontInfo:
    def test_dataclass_defaults(self):
        fi = FontInfo(path=BUNDLED_FONT, format="truetype")
        assert fi.family_name == ""
        assert fi.style_name == ""
        assert fi.glyph_count == 0
        assert fi.codepoints == set()
        assert fi.font_number == 0


class TestReadFont:
    def test_read_bundled_font(self):
        if not BUNDLED_FONT.exists():
            pytest.skip("Bundled font not found")
        fi = read_font(str(BUNDLED_FONT))
        assert fi.family_name == "JetBrains Mono"
        assert fi.style_name == "Regular"
        assert fi.glyph_count > 0
        assert len(fi.codepoints) > 0
        assert fi.font_number == 0

    def test_read_font_with_number(self):
        if not BUNDLED_FONT.exists():
            pytest.skip("Bundled font not found")
        fi = read_font(str(BUNDLED_FONT), font_number=0)
        assert fi.format in ("truetype", "opentype", "woff", "woff2")

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            read_font("/nonexistent/path/font.ttf")


class TestDeduceFormat:
    def test_woff2_flavor(self):
        class MockFont:
            flavor = "woff2"

            def __contains__(self, _):
                return False

        assert _deduce_format(MockFont())  # type: ignore[reportArgumentType] == "woff2"  # type: ignore[reportArgumentType]

    def test_woff_flavor(self):
        class MockFont:
            flavor = "woff"

            def __contains__(self, _):
                return False

        assert _deduce_format(MockFont())  # type: ignore[reportArgumentType] == "woff"

    def test_cff_opentype(self):
        class MockFont:
            flavor = None

            def __contains__(self, item):
                return item in ("CFF ",)

        assert _deduce_format(MockFont())  # type: ignore[reportArgumentType] == "opentype"

    def test_gsub_opentype(self):
        class MockFont:
            flavor = None

            def __contains__(self, item):
                return item == "GSUB"

        assert _deduce_format(MockFont())  # type: ignore[reportArgumentType] == "opentype"

    def test_gpos_opentype(self):
        class MockFont:
            flavor = None

            def __contains__(self, item):
                return item == "GPOS"

        assert _deduce_format(MockFont())  # type: ignore[reportArgumentType] == "opentype"

    def test_plain_truetype(self):
        class MockFont:
            flavor = None

            def __contains__(self, _):
                return False

        assert _deduce_format(MockFont())  # type: ignore[reportArgumentType] == "truetype"
