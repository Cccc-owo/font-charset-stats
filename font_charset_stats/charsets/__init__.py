from font_charset_stats.charsets.base import CharSet

_all_charsets: dict[str, CharSet] = {}


def register(charset: CharSet) -> CharSet:
    _all_charsets[charset.name] = charset
    return charset


def get_charset(name: str) -> CharSet:
    if name not in _all_charsets:
        available = ", ".join(sorted(_all_charsets.keys()))
        raise KeyError(f"Unknown charset: {name!r}. Available: {available}")
    return _all_charsets[name]


def list_charsets() -> list[str]:
    return sorted(_all_charsets.keys())


ALL_CHARSETS = _all_charsets

import font_charset_stats.charsets.big5  # noqa: E402, F401
import font_charset_stats.charsets.cjk  # noqa: E402, F401
import font_charset_stats.charsets.cns  # noqa: E402, F401
import font_charset_stats.charsets.gb  # noqa: E402, F401
import font_charset_stats.charsets.gb12345  # noqa: E402, F401
import font_charset_stats.charsets.japanese  # noqa: E402, F401
import font_charset_stats.charsets.jis  # noqa: E402, F401
import font_charset_stats.charsets.korean  # noqa: E402, F401
import font_charset_stats.charsets.latin  # noqa: E402, F401
