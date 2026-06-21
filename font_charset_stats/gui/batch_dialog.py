"""Batch analysis dialog for processing a directory of font files."""

from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QProgressBar,
    QFileDialog,
    QDialogButtonBox,
    QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from font_charset_stats.analyzer import CoverageResult
from font_charset_stats.charsets import ALL_CHARSETS, list_charsets
from font_charset_stats.font_reader import read_font
from font_charset_stats.gui import SUPPORTED_EXTS


class BatchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: dict[str, list[CoverageResult]] = {}

        self.setWindowTitle("Batch Analyze")
        self.resize(900, 500)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Directory:"))
        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText("Select a directory containing font files...")
        dir_layout.addWidget(self._dir_edit)
        self._browse_btn = QPushButton("Browse...")
        dir_layout.addWidget(self._browse_btn)
        layout.addLayout(dir_layout)

        self._run_btn = QPushButton("Run Batch Analysis")
        layout.addWidget(self._run_btn)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(
            ["Font", "Best Coverage", "Charset", "Total Codepoints"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self._table)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _connect_signals(self):
        self._browse_btn.clicked.connect(self._on_browse)
        self._run_btn.clicked.connect(self._on_run)

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Font Directory")
        if path:
            self._dir_edit.setText(path)

    def _on_run(self):
        directory = self._dir_edit.text().strip()
        if not directory:
            return

        font_files = []
        for fp in Path(directory).iterdir():
            if fp.is_file() and fp.suffix.lower() in SUPPORTED_EXTS:
                font_files.append(fp)

        if not font_files:
            self._show_no_fonts()
            return

        self._table.setRowCount(0)
        self._progress.setVisible(True)
        self._progress.setMaximum(len(font_files))
        self._progress.setValue(0)

        charset_list = [ALL_CHARSETS[n] for n in list_charsets()]

        for i, fp in enumerate(font_files):
            try:
                font_info = read_font(str(fp))
                from font_charset_stats.analyzer import analyze

                results = analyze(font_info.codepoints, charset_list)

                best = max(results, key=lambda r: r.coverage) if results else None

                row = self._table.rowCount()
                self._table.insertRow(row)

                name_item = QTableWidgetItem(font_info.family_name or fp.stem)
                name_item.setData(Qt.UserRole, str(fp))
                self._table.setItem(row, 0, name_item)

                if best:
                    pct_item = QTableWidgetItem(f"{best.coverage * 100:.1f}%")
                    pct = best.coverage
                    if pct >= 0.99:
                        pct_item.setBackground(Qt.green)
                    elif pct >= 0.7:
                        pct_item.setBackground(QColor(255, 255, 200))
                    else:
                        pct_item.setBackground(Qt.red)
                    self._table.setItem(row, 1, pct_item)
                    self._table.setItem(row, 2, QTableWidgetItem(best.name))
                else:
                    self._table.setItem(row, 1, QTableWidgetItem("N/A"))
                    self._table.setItem(row, 2, QTableWidgetItem("-"))

                self._table.setItem(
                    row, 3, QTableWidgetItem(str(len(font_info.codepoints)))
                )

                self._results[str(fp)] = results

            except Exception as e:
                row = self._table.rowCount()
                self._table.insertRow(row)
                self._table.setItem(row, 0, QTableWidgetItem(fp.name))
                self._table.setItem(row, 1, QTableWidgetItem(f"Error: {e}"))

            self._progress.setValue(i + 1)
            QApplication.processEvents()

        self._progress.setVisible(False)

    def _show_no_fonts(self):
        self._table.setRowCount(1)
        no_item = QTableWidgetItem("No supported font files found in this directory")
        no_item.setBackground(QColor(255, 200, 150))
        self._table.setItem(0, 0, no_item)
