"""Font list panel with drag-and-drop support."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListView,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from font_charset_stats.font_reader import FontInfo
from font_charset_stats.gui import SUPPORTED_EXTS
from font_charset_stats.gui.models import FontListModel


class FontListPanel(QGroupBox):
    font_added = Signal(object)
    font_removed = Signal(int)
    fonts_changed = Signal()
    variant_changed = Signal(int, int)  # font_index, font_number
    system_fonts_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(self.tr("Fonts"), parent)
        self._variants: dict[int, list[tuple[int, str, str, int]]] = {}
        self._setup_ui()
        self.setAcceptDrops(True)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._model = FontListModel(self)
        self._view = QListView()
        self._view.setModel(self._model)
        self._view.setSelectionMode(QListView.ExtendedSelection)
        self._view.setAlternatingRowColors(True)
        self._view.selectionModel().selectionChanged.connect(self._on_selection_changed)

        variant_layout = QHBoxLayout()
        self._variant_label = QLabel(self.tr("Variant:"))
        variant_layout.addWidget(self._variant_label)
        self._variant_combo = QComboBox()
        self._variant_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._variant_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._variant_combo.setMinimumWidth(160)
        self._variant_combo.setEnabled(False)
        self._variant_combo.currentIndexChanged.connect(self._on_variant_selected)
        variant_layout.addWidget(self._variant_combo)

        btn_layout = QHBoxLayout()
        self._add_btn = QPushButton(self.tr("Add"))
        self._remove_btn = QPushButton(self.tr("Remove"))
        self._system_btn = QPushButton(self.tr("System Fonts..."))

        self._add_btn.clicked.connect(self._on_add)
        self._remove_btn.clicked.connect(self._on_remove)
        self._system_btn.clicked.connect(self._on_system_fonts)

        btn_layout.addWidget(self._add_btn)
        btn_layout.addWidget(self._remove_btn)
        btn_layout.addWidget(self._system_btn)
        btn_layout.addStretch()

        layout.addWidget(self._view)
        layout.addLayout(variant_layout)
        layout.addLayout(btn_layout)

    def _on_system_fonts(self):
        self.system_fonts_requested.emit()

    def retranslate(self):
        self.setTitle(self.tr("Fonts"))
        self._variant_label.setText(self.tr("Variant:"))
        self._add_btn.setText(self.tr("Add"))
        self._remove_btn.setText(self.tr("Remove"))
        self._system_btn.setText(self.tr("System Fonts..."))

    def _on_add(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("Open Font Files"),
            "",
            self.tr("Font Files (*.ttf *.otf *.woff *.woff2);;All Files (*)"),
        )
        for p in paths:
            self.font_added.emit(p)

    def _on_remove(self):
        indexes = self._view.selectedIndexes()
        rows = sorted({idx.row() for idx in indexes}, reverse=True)
        for row in rows:
            self._model.remove_font(row)
            self._variants.pop(row, None)
            self.font_removed.emit(row)
        if rows:
            self._update_variant_combo()
            self.fonts_changed.emit()

    def _on_selection_changed(self):
        self._update_variant_combo()

    def _update_variant_combo(self):
        self._variant_combo.blockSignals(True)
        self._variant_combo.clear()
        indexes = self._view.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            variants = self._variants.get(row, [])
            if variants:
                for num, family, style, weight_val in variants:
                    self._variant_combo.addItem(f"{family} — {style} (w{weight_val})", num)
                self._variant_combo.setEnabled(True)
            else:
                self._variant_combo.setEnabled(False)
        else:
            self._variant_combo.setEnabled(False)
        self._variant_combo.blockSignals(False)

    def _on_variant_selected(self, idx: int):
        if not self._variant_combo.isEnabled():
            return
        indexes = self._view.selectedIndexes()
        if not indexes:
            return
        row = indexes[0].row()
        face_num = self._variant_combo.currentData()
        if face_num is not None:
            self.variant_changed.emit(row, face_num)

    def add_font_info(self, font_info: FontInfo, variants=None):
        row = self._model.rowCount()
        self._model.add_font(font_info)
        if variants:
            self._variants[row] = variants
        self.fonts_changed.emit()

    def remove_font_at(self, row: int):
        self._model.remove_font(row)
        self._variants.pop(row, None)
        self.font_removed.emit(row)
        self._update_variant_combo()
        self.fonts_changed.emit()

    def fonts(self) -> list[FontInfo]:
        return self._model.fonts()

    def clear(self):
        self._model.clear()
        self._variants.clear()
        self.fonts_changed.emit()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for url in urls:
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_EXTS:
                self.font_added.emit(str(path))
        event.acceptProposedAction()
