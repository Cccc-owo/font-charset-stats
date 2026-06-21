"""Qt models for font-charset-stats GUI."""

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

from font_charset_stats.analyzer import CoverageResult
from font_charset_stats.font_reader import FontInfo
from font_charset_stats.gui.theme import COVERAGE_FG, coverage_bg_color


class FontListModel(QAbstractTableModel):
    """Model for loaded font list: family name, style, format, glyphs, codepoints."""

    _COLUMNS = ("Family", "Style", "Format", "Glyphs", "Codepoints")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fonts: list[FontInfo] = []

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None):
        if parent is None:
            parent = QModelIndex()
        return len(self._fonts) if not parent.isValid() else 0

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex | None = None):
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
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
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

        if n_charsets > 0 and len(self._fonts) > 0:
            assert len(results) == len(self._fonts) * n_charsets, (
                f"Results count {len(results)} != fonts {len(self._fonts)} × charsets {n_charsets}"
            )

        self._cells = []
        for _cs_idx, cs_name in enumerate(self._charset_names):
            row_cells: list[_Cell] = []
            for fi, _font in enumerate(fonts):
                start = fi * n_charsets
                font_results = results[start : start + n_charsets] if start < len(results) else []
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

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None):
        if parent is None:
            parent = QModelIndex()
        return len(self._charset_names) if not parent.isValid() else 0

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex | None = None):
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
            return coverage_bg_color(cell.coverage)
        if role == Qt.ItemDataRole.ForegroundRole:
            return COVERAGE_FG
        if role == Qt.ItemDataRole.ToolTipRole:
            return f"{cell.charset_desc}\nMatched: {cell.matched:,d} / Total: {cell.total:,d}"
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
            and 0 <= section < len(self._fonts)
        ):
            return self._fonts[section].family_name or self._fonts[section].path.name
        if orientation == Qt.Orientation.Vertical and 0 <= section < len(self._charset_names):
            if role == Qt.ItemDataRole.DisplayRole:
                return self._charset_names[section]
            if role == Qt.ItemDataRole.ToolTipRole:
                return self._charset_descs[section]
        return None

    def cell_at(self, row: int, col: int) -> _Cell:
        return self._cells[row][col]
