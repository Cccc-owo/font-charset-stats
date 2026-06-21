"""Qt models for font-charset-stats GUI."""

import unicodedata
from dataclasses import dataclass
from typing import Optional, Union

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QColor

from font_charset_stats.analyzer import CoverageResult
from font_charset_stats.font_reader import FontInfo


class FontListModel(QAbstractTableModel):
    """Model for loaded font list: family name, style, format, glyphs, codepoints."""

    _COLUMNS = ("Family", "Style", "Format", "Glyphs", "Codepoints")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fonts: list[FontInfo] = []

    def rowCount(
        self, parent: Optional[Union[QModelIndex, QPersistentModelIndex]] = None
    ):
        if parent is None:
            parent = QModelIndex()
        return len(self._fonts) if not parent.isValid() else 0

    def columnCount(
        self, parent: Optional[Union[QModelIndex, QPersistentModelIndex]] = None
    ):
        if parent is None:
            parent = QModelIndex()
        return len(self._COLUMNS) if not parent.isValid() else 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        font = self._fonts[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return font.family_name
            elif col == 1:
                return font.style_name
            elif col == 2:
                return font.format
            elif col == 3:
                return str(font.glyph_count)
            elif col == 4:
                return str(len(font.codepoints))
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self._COLUMNS[section]
        return None

    def add_font(self, font_info: FontInfo):
        row = len(self._fonts)
        self.beginInsertRows(QModelIndex(), row, row)
        self._fonts.append(font_info)
        self.endInsertRows()

    def remove_font(self, row: int):
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._fonts[row]
        self.endRemoveRows()

    def font_at(self, row: int) -> FontInfo:
        return self._fonts[row]

    def fonts(self) -> list[FontInfo]:
        return list(self._fonts)

    def clear(self):
        self.beginResetModel()
        self._fonts.clear()
        self.endResetModel()


@dataclass
class _Cell:
    coverage: float
    matched: int = 0
    total: int = 0
    charset_name: str = ""
    charset_desc: str = ""


def _bg_color(pct: float) -> QColor:
    if pct >= 0.99:
        return QColor(198, 239, 206)  # soft green
    elif pct >= 0.9:
        return QColor(217, 240, 180)  # light green
    elif pct >= 0.7:
        return QColor(255, 243, 160)  # light yellow
    elif pct >= 0.5:
        return QColor(255, 210, 160)  # light orange
    else:
        return QColor(255, 170, 160)  # light red


class CoverageTableModel(QAbstractTableModel):
    """Pivot model: rows=charsets, cols=fonts, cells=coverage %."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fonts: list[FontInfo] = []
        self._charset_names: list[str] = []
        self._charset_descs: list[str] = []
        self._cells: list[list[_Cell]] = []

    def set_data(self, fonts: list[FontInfo], results: list[CoverageResult]):
        self.beginResetModel()
        self._fonts = fonts

        seen: dict[str, str] = {}
        for r in results:
            if r.name not in seen:
                seen[r.name] = r.description
        self._charset_names = list(seen.keys())
        self._charset_descs = [seen[n] for n in self._charset_names]
        n_charsets = len(self._charset_names)

        self._cells = []
        for cs_idx, cs_name in enumerate(self._charset_names):
            row_cells: list[_Cell] = []
            for fi, font in enumerate(fonts):
                start = fi * n_charsets
                font_results = (
                    results[start : start + n_charsets] if start < len(results) else []
                )
                r = next((r for r in font_results if r.name == cs_name), None)
                cell = _Cell(
                    coverage=r.coverage if r else 0.0,
                    matched=r.matched if r else 0,
                    total=r.total if r else 0,
                    charset_name=cs_name,
                    charset_desc=r.description if r else "",
                )
                row_cells.append(cell)
            self._cells.append(row_cells)
        self.endResetModel()

    def rowCount(
        self, parent: Optional[Union[QModelIndex, QPersistentModelIndex]] = None
    ):
        if parent is None:
            parent = QModelIndex()
        return len(self._charset_names) if not parent.isValid() else 0

    def columnCount(
        self, parent: Optional[Union[QModelIndex, QPersistentModelIndex]] = None
    ):
        if parent is None:
            parent = QModelIndex()
        return len(self._fonts) if not parent.isValid() else 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        cell = self._cells[index.row()][index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            return f"{cell.matched:,d}/{cell.total:,d}  ({cell.coverage * 100:.1f}%)"
        if role == Qt.ItemDataRole.BackgroundRole:
            return _bg_color(cell.coverage)
        if role == Qt.ItemDataRole.ForegroundRole:
            return QColor(30, 30, 30)
        if role == Qt.ItemDataRole.ToolTipRole:
            return f"{cell.charset_desc}\nMatched: {cell.matched:,d} / Total: {cell.total:,d}"
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            if 0 <= section < len(self._fonts):
                return (
                    self._fonts[section].family_name or self._fonts[section].path.name
                )
        if orientation == Qt.Orientation.Vertical:
            if 0 <= section < len(self._charset_names):
                if role == Qt.ItemDataRole.DisplayRole:
                    return self._charset_names[section]
                if role == Qt.ItemDataRole.ToolTipRole:
                    return self._charset_descs[section]
        return None

    def cell_at(self, row: int, col: int) -> _Cell:
        return self._cells[row][col]


def _format_codepoint_char(cp: int) -> str:
    if 0xD800 <= cp <= 0xDFFF:
        return "(surrogate)"
    if 0xFDD0 <= cp <= 0xFDEF or cp & 0xFFFE == 0xFFFE:
        return "(nonchar)"
    if cp <= 0x1F or (0x7F <= cp <= 0x9F):
        return "(control)"
    try:
        ch = chr(cp)
        cat = unicodedata.category(ch)
        if cat.startswith("C"):
            return "(control)"
        return ch
    except (ValueError, OverflowError):
        return ""


class MissingCharsetModel(QAbstractTableModel):
    """Flat model listing missing codepoints for a single charset."""

    _COLUMNS = ("Codepoint", "Character")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._missing: list[int] = []

    def set_missing(self, missing: list[int]):
        self.beginResetModel()
        self._missing = missing
        self.endResetModel()

    def rowCount(
        self, parent: Optional[Union[QModelIndex, QPersistentModelIndex]] = None
    ):
        if parent is None:
            parent = QModelIndex()
        return len(self._missing) if not parent.isValid() else 0

    def columnCount(
        self, parent: Optional[Union[QModelIndex, QPersistentModelIndex]] = None
    ):
        if parent is None:
            parent = QModelIndex()
        return 2 if not parent.isValid() else 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        cp = self._missing[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return f"U+{cp:04X}"
            elif col == 1:
                return _format_codepoint_char(cp)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self._COLUMNS[section]
        return None
