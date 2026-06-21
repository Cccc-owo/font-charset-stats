"""Export dialog for saving analysis results as CSV."""

import csv

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from font_charset_stats.analyzer import CoverageResult
from font_charset_stats.font_reader import FontInfo


def _build_csv_rows(fonts: list[FontInfo], results: list[CoverageResult]) -> list[dict]:
    n_charsets = len({r.name for r in results})
    rows: list[dict] = []

    for fi, font in enumerate(fonts):
        font_name = font.family_name or font.path.stem
        start = fi * n_charsets
        font_results = results[start : start + n_charsets] if start < len(results) else []

        for r in font_results:
            rows.append(
                {
                    "Font": font_name,
                    "Path": str(font.path),
                    "Format": font.format,
                    "Glyphs": font.glyph_count,
                    "Codepoints": len(font.codepoints),
                    "Charset": r.name,
                    "Total": r.total,
                    "Matched": r.matched,
                    "Coverage": round(r.coverage * 100, 2),
                }
            )

    return rows


class ExportDialog(QDialog):
    def __init__(self, fonts: list[FontInfo], results: list[CoverageResult], parent=None):
        super().__init__(parent)
        self._fonts = fonts
        self._results = results

        self.setWindowTitle(self.tr("Export Report"))
        self.resize(500, 120)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel(self.tr("Save to:")))
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText(self.tr("Select output file path..."))
        file_layout.addWidget(self._path_edit)
        self._browse_btn = QPushButton(self.tr("Browse..."))
        self._browse_btn.clicked.connect(self._on_browse)
        file_layout.addWidget(self._browse_btn)
        layout.addLayout(file_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_export)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_browse(self):
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save Report"), "", self.tr("CSV Files (*.csv)")
        )
        if path:
            if not path.lower().endswith(".csv"):
                path += ".csv"
            self._path_edit.setText(path)

    def _on_export(self):
        path = self._path_edit.text().strip()
        if not path:
            QMessageBox.warning(
                self, self.tr("Export"), self.tr("Please select an output file path.")
            )
            return

        try:
            rows = _build_csv_rows(self._fonts, self._results)
            if not rows:
                QMessageBox.warning(self, self.tr("Export"), self.tr("No data to export."))
                return

            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            QMessageBox.information(self, self.tr("Export"), self.tr("Report saved to:\n%s") % path)
            self.accept()
        except OSError as e:
            QMessageBox.critical(self, self.tr("Export Error"), str(e))
