"""Charset selection panel with checkboxes and search filter."""

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from font_charset_stats.charsets import get_charset
from font_charset_stats.charsets.base import CharSet

_WESTERN_CUTOFF = "Dingbats"

_CHARSET_ORDER = [
    # ── Latin / Western ──
    "Basic Latin",
    "Latin-1 Supplement",
    "Latin Extended-A",
    "Latin Extended-B",
    "IPA Extensions",
    "Spacing Modifier",
    "Combining Diacritical",
    # ── Greek / Cyrillic ──
    "Greek and Coptic",
    "Cyrillic",
    "Cyrillic Supplement",
    # ── Punctuation / Symbols ──
    "General Punctuation",
    "Superscript/Subscript",
    "Currency Symbols",
    "Letterlike Symbols",
    "Number Forms",
    "Arrows",
    "Mathematical Operators",
    # ── Drawing / Shapes ──
    "Box Drawing",
    "Block Elements",
    "Geometric Shapes",
    "Miscellaneous Symbols",
    "Dingbats",
    # ── Chinese ──
    "GB2312",
    "GBK",
    "GB18030-Level1",
    "GB18030-Level2",
    "GB18030-Level3",
    "GB12345",
    "Big5",
    "Big5-HKSCS",
    "CNS11643",
    # ── Japanese ──
    "JIS0208-Level1",
    "JIS0208-Level2",
    "JIS0213",
    "Japanese-Hiragana",
    "Japanese-Katakana",
    # ── Korean ──
    "KSX1001-Hanja",
    "Korean-Hangul",
    "Korean-Jamo",
    # ── CJK Unicode Blocks ──
    "CJK-Basic",
    "CJK-Compat",
    "CJK-CompatSup",
    "CJK-ExtA",
    "CJK-ExtB",
    "CJK-ExtC",
    "CJK-ExtD",
    "CJK-ExtE",
    "CJK-ExtF",
    "CJK-ExtG",
    "CJK-ExtH",
    "CJK-ExtI",
]

_WESTERN_NAMES = set(_CHARSET_ORDER[: _CHARSET_ORDER.index(_WESTERN_CUTOFF) + 1])


class CharsetPanel(QGroupBox):
    selection_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(self.tr("Charsets"), parent)
        self._all_items: list[QListWidgetItem] = []
        self._setup_ui()
        self._populate()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._filter = QLineEdit()
        self._filter.setPlaceholderText(self.tr("Filter charsets..."))
        self._filter.textChanged.connect(self._apply_filter)

        self._western_cb = QCheckBox(self.tr("Show Western Unicode Blocks"))
        self._western_cb.toggled.connect(self._on_western_toggled)
        layout.addWidget(self._western_cb)

        self._list = QListWidget()

        btn_layout = QHBoxLayout()
        self._select_all_btn = QPushButton(self.tr("Select All"))
        self._deselect_all_btn = QPushButton(self.tr("Deselect All"))
        self._select_all_btn.clicked.connect(self._select_all)
        self._deselect_all_btn.clicked.connect(self._deselect_all)
        btn_layout.addWidget(self._select_all_btn)
        btn_layout.addWidget(self._deselect_all_btn)

        layout.addWidget(self._filter)
        layout.addWidget(self._list)
        layout.addLayout(btn_layout)

    def _populate(self):
        for name in _CHARSET_ORDER:
            cs = get_charset(name)
            item = QListWidgetItem(f"{name}  ({cs.total:,d} cp)")
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setToolTip(cs.description)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self._list.addItem(item)
            self._all_items.append(item)
        self._apply_western_filter()

    def _on_western_toggled(self):
        self._apply_all_filters()
        self.selection_changed.emit()

    def _apply_all_filters(self):
        show_western = self._western_cb.isChecked()
        filter_text = self._filter.text().lower()
        for item in self._all_items:
            name = item.data(Qt.ItemDataRole.UserRole)
            hidden = False
            if not show_western and name in _WESTERN_NAMES:
                hidden = True
            if filter_text and filter_text not in item.text().lower():
                hidden = True
            item.setHidden(hidden)

    def _apply_filter(self, _text: str):
        self._apply_all_filters()

    def _select_all(self):
        for item in self._all_items:
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Checked)
        self.selection_changed.emit()

    def _deselect_all(self):
        for item in self._all_items:
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Unchecked)
        self.selection_changed.emit()

    def retranslate(self):
        self.setTitle(self.tr("Charsets"))
        self._filter.setPlaceholderText(self.tr("Filter charsets..."))
        self._western_cb.setText(self.tr("Show Western Unicode Blocks"))
        self._select_all_btn.setText(self.tr("Select All"))
        self._deselect_all_btn.setText(self.tr("Deselect All"))

    def selected_charsets(self) -> list[CharSet]:
        result: list[CharSet] = []
        for item in self._all_items:
            if item.isHidden():
                continue
            if item.checkState() == Qt.CheckState.Checked:
                name = item.data(Qt.UserRole)
                try:
                    result.append(get_charset(name))
                except KeyError:
                    logging.getLogger(__name__).warning("Charset not found in registry: %s", name)
        return result

    def selected_names(self) -> list[str]:
        return [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self._all_items
            if not item.isHidden() and item.checkState() == Qt.CheckState.Checked
        ]
