"""Results view with coverage table, charts, missing chars, and font preview."""

import bisect
import contextlib
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableView,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from font_charset_stats.analyzer import CoverageResult
from font_charset_stats.charsets import get_charset
from font_charset_stats.font_reader import FontInfo
from font_charset_stats.gui.models import CoverageTableModel
from font_charset_stats.gui.theme import CHART_COLORS, CHART_TEXT_COLOR

_UNICODE_BLOCKS: list[tuple[str, int, int]] = [
    ("Basic Latin", 0x0000, 0x007F),
    ("Latin-1 Supplement", 0x0080, 0x00FF),
    ("Latin Extended-A", 0x0100, 0x017F),
    ("Latin Extended-B", 0x0180, 0x024F),
    ("IPA Extensions", 0x0250, 0x02AF),
    ("Spacing Modifier Letters", 0x02B0, 0x02FF),
    ("Combining Diacritical Marks", 0x0300, 0x036F),
    ("Greek and Coptic", 0x0370, 0x03FF),
    ("Cyrillic", 0x0400, 0x04FF),
    ("Cyrillic Supplement", 0x0500, 0x052F),
    ("Armenian", 0x0530, 0x058F),
    ("Hebrew", 0x0590, 0x05FF),
    ("Arabic", 0x0600, 0x06FF),
    ("Devanagari", 0x0900, 0x097F),
    ("Bengali", 0x0980, 0x09FF),
    ("Gurmukhi", 0x0A00, 0x0A7F),
    ("Gujarati", 0x0A80, 0x0AFF),
    ("Tamil", 0x0B80, 0x0BFF),
    ("Telugu", 0x0C00, 0x0C7F),
    ("Kannada", 0x0C80, 0x0CFF),
    ("Malayalam", 0x0D00, 0x0D7F),
    ("Thai", 0x0E00, 0x0E7F),
    ("Lao", 0x0E80, 0x0EFF),
    ("Tibetan", 0x0F00, 0x0FFF),
    ("Myanmar", 0x1000, 0x109F),
    ("Georgian", 0x10A0, 0x10FF),
    ("Hangul Jamo", 0x1100, 0x11FF),
    ("Ethiopic", 0x1200, 0x137F),
    ("Cherokee", 0x13A0, 0x13FF),
    ("Unified Canadian Aboriginal Syllabics", 0x1400, 0x167F),
    ("Ogham", 0x1680, 0x169F),
    ("Runic", 0x16A0, 0x16FF),
    ("Khmer", 0x1780, 0x17FF),
    ("Mongolian", 0x1800, 0x18AF),
    ("Latin Extended Additional", 0x1E00, 0x1EFF),
    ("Greek Extended", 0x1F00, 0x1FFF),
    ("General Punctuation", 0x2000, 0x206F),
    ("Superscripts and Subscripts", 0x2070, 0x209F),
    ("Currency Symbols", 0x20A0, 0x20CF),
    ("Letterlike Symbols", 0x2100, 0x214F),
    ("Number Forms", 0x2150, 0x218F),
    ("Arrows", 0x2190, 0x21FF),
    ("Mathematical Operators", 0x2200, 0x22FF),
    ("Miscellaneous Technical", 0x2300, 0x23FF),
    ("Control Pictures", 0x2400, 0x243F),
    ("Enclosed Alphanumerics", 0x2460, 0x24FF),
    ("Box Drawing", 0x2500, 0x257F),
    ("Block Elements", 0x2580, 0x259F),
    ("Geometric Shapes", 0x25A0, 0x25FF),
    ("Miscellaneous Symbols", 0x2600, 0x26FF),
    ("Dingbats", 0x2700, 0x27BF),
    ("Braille Patterns", 0x2800, 0x28FF),
    ("CJK Radicals Supplement", 0x2E80, 0x2EFF),
    ("Kangxi Radicals", 0x2F00, 0x2FDF),
    ("Ideographic Description Characters", 0x2FF0, 0x2FFF),
    ("CJK Symbols and Punctuation", 0x3000, 0x303F),
    ("Hiragana", 0x3040, 0x309F),
    ("Katakana", 0x30A0, 0x30FF),
    ("Bopomofo", 0x3100, 0x312F),
    ("Hangul Compatibility Jamo", 0x3130, 0x318F),
    ("Kanbun", 0x3190, 0x319F),
    ("CJK Strokes", 0x31C0, 0x31EF),
    ("Katakana Phonetic Extensions", 0x31F0, 0x31FF),
    ("Enclosed CJK Letters and Months", 0x3200, 0x32FF),
    ("CJK Compatibility", 0x3300, 0x33FF),
    ("CJK Unified Ideographs Extension A", 0x3400, 0x4DBF),
    ("Yijing Hexagram Symbols", 0x4DC0, 0x4DFF),
    ("CJK Unified Ideographs", 0x4E00, 0x9FFF),
    ("Yi Syllables", 0xA000, 0xA48F),
    ("Hangul Syllables", 0xAC00, 0xD7AF),
    ("Private Use Area", 0xE000, 0xF8FF),
    ("CJK Compatibility Ideographs", 0xF900, 0xFAFF),
    ("Alphabetic Presentation Forms", 0xFB00, 0xFB4F),
    ("Arabic Presentation Forms-A", 0xFB50, 0xFDFF),
    ("CJK Compatibility Forms", 0xFE30, 0xFE4F),
    ("Halfwidth and Fullwidth Forms", 0xFF00, 0xFFEF),
    ("Linear B Syllabary", 0x10000, 0x1007F),
    ("CJK Unified Ideographs Extension B", 0x20000, 0x2A6DF),
    ("CJK Unified Ideographs Extension C", 0x2A700, 0x2B73F),
    ("CJK Unified Ideographs Extension D", 0x2B740, 0x2B81F),
    ("CJK Unified Ideographs Extension E", 0x2B820, 0x2CEAF),
    ("CJK Unified Ideographs Extension F", 0x2CEB0, 0x2EBEF),
    ("CJK Compatibility Ideographs Supplement", 0x2F800, 0x2FA1F),
    ("Supplementary Private Use Area-A", 0xF0000, 0xFFFFF),
    ("Supplementary Private Use Area-B", 0x100000, 0x10FFFF),
]

_BLOCK_KEYS: list[tuple[int, int, int]] = []
for idx, (_, lo, hi) in enumerate(_UNICODE_BLOCKS):
    _BLOCK_KEYS.append((lo, hi, idx))
_BLOCK_STARTS = [k[0] for k in _BLOCK_KEYS]


def _block_for(cp: int) -> str:
    i = bisect.bisect_right(_BLOCK_STARTS, cp) - 1
    if i >= 0 and _BLOCK_KEYS[i][0] <= cp <= _BLOCK_KEYS[i][1]:
        return _UNICODE_BLOCKS[_BLOCK_KEYS[i][2]][0]
    lo = cp & ~0xFF
    hi = lo | 0xFF
    return f"U+{lo:04X}-U+{hi:04X}"


def _group_missing_by_block(missing: list[int]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    for cp in missing:
        block = _block_for(cp)
        groups.setdefault(block, []).append(cp)
    return groups


try:
    import matplotlib
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
    from matplotlib.font_manager import FontProperties, fontManager

    _BUNDLED_FONT = Path(__file__).resolve().parent / "fonts" / "JetBrainsMono-Regular.ttf"
    _USER_FONT_PATH: str | None = None

    def _get_chart_font():  # type: ignore[reportOptionalCall]
        if _BUNDLED_FONT.exists():
            return FontProperties(fname=str(_BUNDLED_FONT))  # type: ignore[reportOptionalCall]
        return FontProperties()  # type: ignore[reportOptionalCall]

    def _register_user_font(font_path: str) -> None:
        global _USER_FONT_PATH
        if font_path == _USER_FONT_PATH:
            return
        _USER_FONT_PATH = font_path
        with contextlib.suppress(Exception):
            fontManager.addfont(font_path)
        fb = ["JetBrains Mono"]
        try:
            for fe in fontManager.ttflist:
                if fe.fname == font_path:
                    fb.insert(0, fe.name)
                    break
        except Exception:
            pass
        matplotlib.rcParams["font.sans-serif"] = fb
        matplotlib.rcParams["font.family"] = "sans-serif"

    def _init_bundled() -> None:
        if _BUNDLED_FONT.exists():
            with contextlib.suppress(Exception):
                fontManager.addfont(str(_BUNDLED_FONT))
        matplotlib.rcParams["font.sans-serif"] = ["JetBrains Mono"]
        matplotlib.rcParams["font.family"] = "sans-serif"

    _init_bundled()
    matplotlib.rcParams["axes.unicode_minus"] = False
    HAS_MPL = True
except ImportError:
    FigureCanvasQTAgg = None  # type: ignore
    Figure = None  # type: ignore
    FontProperties = None  # type: ignore
    HAS_MPL = False


def _preview_sample_text() -> str:
    return (
        "天地玄黄 宇宙洪荒 日月盈昃 辰宿列張 寒來暑往 秋收冬藏\n"
        "こんにちは 世界 日本語のフォントプレビュー\n"
        "The quick brown fox jumps over the lazy dog.\n"
        "0123456789 !@#$%^&*()"
    )


class ResultsView(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fonts: list[FontInfo] = []
        self._results: list[CoverageResult] = []
        self._font_families: dict[str, str] = {}
        self._charset_order: list[str] = []

        self._setup_coverage_tab()
        if HAS_MPL:
            self._setup_chart_tab()
        self._setup_missing_tab()
        self._setup_preview_tab()

        self._missing_tab_idx = self.indexOf(self._missing_widget)
        self.currentChanged.connect(self._on_tab_changed)

    def _setup_coverage_tab(self):
        self._coverage_table = QTableView()
        self._coverage_model = CoverageTableModel(self)
        self._coverage_table.setModel(self._coverage_model)
        self._coverage_table.horizontalHeader().setStretchLastSection(True)
        self._coverage_table.verticalHeader().setStretchLastSection(True)
        self._coverage_table.setAlternatingRowColors(True)
        self._coverage_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.addTab(self._coverage_table, "Coverage")

    def _setup_chart_tab(self) -> None:
        assert Figure is not None and FigureCanvasQTAgg is not None
        self._figure = Figure(figsize=(6, 4), dpi=100)
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._ax = self._figure.add_subplot(111)
        self.addTab(self._canvas, "Chart")

    def _setup_missing_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._missing_summary = QLabel("")
        layout.addWidget(self._missing_summary)

        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Charset:"))
        self._missing_charset_combo = QComboBox()
        self._missing_charset_combo.currentTextChanged.connect(self._update_missing_view)
        selector_layout.addWidget(self._missing_charset_combo)
        selector_layout.addWidget(QLabel("Font:"))
        self._missing_font_combo = QComboBox()
        self._missing_font_combo.currentIndexChanged.connect(self._update_missing_view)
        selector_layout.addWidget(self._missing_font_combo)

        self._show_ctrl_cb = QCheckBox("Show Controls")
        self._show_ctrl_cb.toggled.connect(self._update_missing_view)
        selector_layout.addWidget(self._show_ctrl_cb)

        selector_layout.addStretch()

        layout.addLayout(selector_layout)

        self._missing_tree = QTreeWidget()
        self._missing_tree.setHeaderLabels(["Codepoint", "Character"])
        self._missing_tree.setAlternatingRowColors(True)
        self._missing_tree.itemExpanded.connect(self._on_missing_expanded)
        layout.addWidget(self._missing_tree)

        self.addTab(widget, "Missing")
        self._missing_widget = widget

    def _setup_preview_tab(self):
        self._preview_text = QTextEdit()
        self._preview_text.setPlaceholderText("Type text to preview with the selected font...")
        self._preview_text.setPlainText(_preview_sample_text())

        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font:"))
        self._preview_font_combo = QComboBox()
        self._preview_font_combo.currentTextChanged.connect(self._update_preview_font)
        font_layout.addWidget(self._preview_font_combo)
        font_layout.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(font_layout)
        layout.addWidget(self._preview_text)

        widget = QWidget()
        widget.setLayout(layout)
        self.addTab(widget, "Preview")

    def set_results(
        self,
        fonts: list[FontInfo],
        results: list[CoverageResult],
        charset_order: list[str] | None = None,
    ):
        self._fonts = fonts
        self._results = results
        self._charset_order = charset_order or []

        if fonts and HAS_MPL:
            _register_user_font(str(fonts[0].path))

        self._coverage_model.set_data(fonts, results)

        if HAS_MPL:
            self._update_chart()

        self._missing_charset_combo.blockSignals(True)
        self._missing_charset_combo.clear()
        if charset_order:
            charset_names = [
                n for n in charset_order if any(r.name == n and r.coverage < 1.0 for r in results)
            ]
        else:
            charset_names = sorted({r.name for r in results if r.coverage < 1.0})
        self._missing_charset_combo.addItems(charset_names or ["(none missing)"])
        self._missing_charset_combo.blockSignals(False)

        self._load_preview_fonts()

        missing_font_names = [f.family_name or f.path.stem for f in fonts]
        self._missing_font_combo.blockSignals(True)
        self._missing_font_combo.clear()
        self._missing_font_combo.addItems(missing_font_names)
        self._missing_font_combo.blockSignals(False)

    def _update_chart(self):
        self._ax.clear()
        if not self._fonts or not self._results:
            self._canvas.draw()
            return

        seen: set[str] = set()
        for r in self._results:
            seen.add(r.name)

        font0_coverage: dict[str, float] = {}
        n_cs = len(seen)
        font0_results = self._results[:n_cs] if len(self._results) >= n_cs else []
        for r in font0_results:
            font0_coverage[r.name] = r.coverage

        order_map = {n: i for i, n in enumerate(self._charset_order)}
        charset_names = sorted(
            seen,
            key=lambda n: (
                -font0_coverage.get(n, 0),
                order_map.get(n, 9999),
                n,
            ),
        )

        import itertools

        import numpy as np

        n_charsets = len(charset_names)
        n_fonts = len(self._fonts)
        bar_width = 0.7 / n_fonts
        indices = np.arange(n_charsets)

        color_cycle = itertools.cycle(CHART_COLORS)

        assert FontProperties is not None
        chart_font = _get_chart_font()

        for fi, (font, color) in enumerate(zip(self._fonts, color_cycle)):
            raw_label = font.family_name or font.path.stem
            font_label = raw_label if len(raw_label) <= 32 else raw_label[:31] + "…"
            start = fi * n_charsets
            font_results = (
                self._results[start : start + n_charsets] if start < len(self._results) else []
            )
            values = []
            for cn in charset_names:
                r = next((r for r in font_results if r.name == cn), None)
                values.append(r.coverage * 100 if r else 0)
            offset = (fi - (n_fonts - 1) / 2) * bar_width
            bars = self._ax.barh(indices + offset, values, bar_width, label=font_label, color=color)
            for bar, val in zip(bars, values):
                if val > 0:
                    self._ax.text(
                        bar.get_width() + 0.3,
                        bar.get_y() + bar.get_height() / 2,
                        f"{val:.1f}",
                        va="center",
                        fontsize=7,
                        fontproperties=chart_font,
                        color=CHART_TEXT_COLOR,
                    )

        self._ax.set_yticks(indices)
        self._ax.set_yticklabels(charset_names, fontsize=9, fontproperties=chart_font)
        self._ax.set_xlabel("Coverage (%)", fontproperties=chart_font)
        self._ax.set_xlim(0, 105)
        self._ax.legend(loc="upper right", fontsize=7, prop=chart_font)
        self._figure.tight_layout()
        self._canvas.draw()

    def _on_tab_changed(self, index: int):
        if index == self._missing_tab_idx and self._fonts:
            self._update_missing_view()

    def _update_missing_view(self):
        charset_name = self._missing_charset_combo.currentText()
        font_idx = self._missing_font_combo.currentIndex()
        if not charset_name or font_idx < 0 or font_idx >= len(self._fonts):
            return
        try:
            cs = get_charset(charset_name)
        except KeyError:
            return

        missing = sorted(cs.codepoints - self._fonts[font_idx].codepoints)
        if not self._show_ctrl_cb.isChecked():
            missing = [cp for cp in missing if not (cp <= 0x1F or 0x7F <= cp <= 0x9F)]
        total = len(missing)
        grouped = _group_missing_by_block(missing)
        self._missing_summary.setText(
            f"Total missing: {total:,d} codepoints  |  {len(grouped)} blocks"
        )

        self._missing_tree.clear()
        for block_name, codepoints in sorted(grouped.items(), key=lambda kv: kv[1][0]):
            codepoints = grouped[block_name]
            count = len(codepoints)
            label = f"{block_name}  ({count:,d})"
            parent = QTreeWidgetItem(self._missing_tree)
            parent.setText(0, label)
            parent.setData(0, Qt.ItemDataRole.UserRole, codepoints)

            if count <= 200:
                self._populate_block_children(parent, codepoints)
            else:
                placeholder = QTreeWidgetItem(parent)
                placeholder.setText(0, "Click to expand...")

        for col in range(2):
            self._missing_tree.resizeColumnToContents(col)

    def _on_missing_expanded(self, item: QTreeWidgetItem):
        if item.childCount() == 1 and item.child(0).text(0) == "Click to expand...":
            item.takeChildren()
            codepoints = item.data(0, Qt.ItemDataRole.UserRole)
            if codepoints:
                self._populate_block_children(item, codepoints)
                for col in range(2):
                    self._missing_tree.resizeColumnToContents(col)

    def _populate_block_children(self, parent: QTreeWidgetItem, codepoints: list[int]):
        for cp in codepoints:
            child = QTreeWidgetItem(parent)
            child.setText(0, f"U+{cp:04X}")
            if 0xD800 <= cp <= 0xDFFF:
                child.setText(1, "(surrogate)")
            elif cp <= 0x1F or (0x7F <= cp <= 0x9F):
                child.setText(1, "(control)")
            elif 0xFDD0 <= cp <= 0xFDEF or cp & 0xFFFE == 0xFFFE:
                child.setText(1, "(nonchar)")
            else:
                try:
                    child.setText(1, chr(cp))
                except (ValueError, OverflowError):
                    child.setText(1, "")

    def _load_preview_fonts(self):
        self._font_families: dict[str, str] = {}

        for font in self._fonts:
            font_id = QFontDatabase.addApplicationFont(str(font.path))
            if font_id < 0:
                continue
            families = QFontDatabase.applicationFontFamilies(font_id)
            if not families:
                continue
            qt_family = families[0]
            label = font.family_name or font.path.stem
            self._font_families[label] = qt_family

        self._preview_font_combo.blockSignals(True)
        self._preview_font_combo.clear()
        items = list(self._font_families.keys())
        self._preview_font_combo.addItems(items)
        self._preview_font_combo.blockSignals(False)

        if items:
            self._preview_font_combo.setCurrentIndex(0)
            if self._preview_font_combo.currentText():
                self._update_preview_font(self._preview_font_combo.currentText())

    def _update_preview_font(self, label: str):
        qt_family = self._font_families.get(label)
        if not qt_family:
            return
        font = QFont(qt_family, 14)
        self._preview_text.selectAll()
        self._preview_text.setCurrentFont(font)
