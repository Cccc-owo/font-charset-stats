"""Translation support for font-charset-stats GUI."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QLocale, QTranslator
from PySide6.QtWidgets import QApplication

_TRANSLATORS: list[QTranslator] = []

_I18N_DIR = Path(__file__).resolve().parent / "i18n"


def _detect_locale() -> str:
    lang = QLocale.system().language()
    if lang == QLocale.Language.Chinese:
        return "zh_CN"
    return ""


def setup_translators(app: QApplication) -> None:
    locale = _detect_locale()
    if locale:
        _load_translator(app, locale)


def switch_language(app: QApplication, locale: str) -> None:
    while _TRANSLATORS:
        t = _TRANSLATORS.pop()
        app.removeTranslator(t)
    if locale:
        _load_translator(app, locale)


def _load_translator(app: QApplication, locale: str) -> None:
    t = QTranslator()
    qm = str(_I18N_DIR / f"font_charset_stats_{locale}.qm")
    if t.load(qm):
        app.installTranslator(t)
        _TRANSLATORS.append(t)
