"""Translation support for font-charset-stats GUI."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QLocale, QTranslator
from PySide6.QtWidgets import QApplication

_TRANSLATORS: list[QTranslator] = []

_I18N_DIR = Path(__file__).resolve().parent / "i18n"


class JsonTranslator(QTranslator):
    def __init__(self, path: str):
        super().__init__()
        self._entries: dict[str, str] = {}
        with open(path, encoding="utf-8") as f:
            data: dict[str, dict[str, str]] = json.load(f)
        for context, messages in data.items():
            for source, translation in messages.items():
                self._entries[f"{context}\x00{source}"] = translation

    def translate(
        self, context: str, source: str, disambiguation: str = "", n: int = -1
    ) -> str | None:
        key = f"{context}\x00{source}"
        if disambiguation:
            key = f"{context}\x00{source}\x00{disambiguation}"
        return self._entries.get(key)


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
    path = _I18N_DIR / f"{locale}.json"
    if path.is_file():
        t = JsonTranslator(str(path))
        app.installTranslator(t)
        _TRANSLATORS.append(t)
