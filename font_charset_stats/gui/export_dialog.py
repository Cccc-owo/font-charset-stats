"""Export dialog for saving analysis results as HTML or PDF."""

from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from font_charset_stats.analyzer import CoverageResult
from font_charset_stats.font_reader import FontInfo
from font_charset_stats.gui.theme import build_html, coverage_css_class


def _build_html(fonts: list[FontInfo], results: list[CoverageResult]) -> str:
    n_charsets = len({r.name for r in results})
    parts: list[str] = []
    for fi, font in enumerate(fonts):
        font_name = font.family_name or font.path.stem
        parts.append(f"<h2>{font_name}</h2>")
        parts.append(f"<p><strong>Path:</strong> {font.path}<br>")
        parts.append(f"<strong>Format:</strong> {font.format} &mdash; ")
        parts.append(f"<strong>Glyphs:</strong> {font.glyph_count:,d} &mdash; ")
        parts.append(f"<strong>Codepoints:</strong> {len(font.codepoints):,d}</p>")

        start = fi * n_charsets
        font_results = results[start : start + n_charsets] if start < len(results) else []
        if not font_results:
            parts.append("<p><em>No results.</em></p>")
            continue

        parts.append("<table><thead><tr>")
        parts.append("<th>Charset</th><th>Total</th><th>Matched</th><th>Coverage</th>")
        parts.append("</tr></thead><tbody>")

        for r in font_results:
            bar_class = coverage_css_class(r.coverage)
            parts.append("<tr>")
            parts.append(f'<td class="name-col">{r.name}</td>')
            parts.append(f"<td>{r.total:,d}</td>")
            parts.append(f"<td>{r.matched:,d}</td>")
            parts.append(
                f'<td><span class="bar {bar_class}" style="width:{r.coverage * 120}px"></span>'
                f"{r.coverage * 100:.2f}%</td>"
            )
            parts.append("</tr>")

        parts.append("</tbody></table>")

    return build_html(content="\n".join(parts))


class ExportDialog(QDialog):
    def __init__(self, fonts: list[FontInfo], results: list[CoverageResult], parent=None):
        super().__init__(parent)
        self._fonts = fonts
        self._results = results

        self.setWindowTitle("Export Report")
        self.resize(500, 200)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("Format:"))
        self._group = QButtonGroup(self)
        self._html_radio = QRadioButton("HTML")
        self._pdf_radio = QRadioButton("PDF")
        self._html_radio.setChecked(True)
        self._group.addButton(self._html_radio, 1)
        self._group.addButton(self._pdf_radio, 2)
        fmt_layout.addWidget(self._html_radio)
        fmt_layout.addWidget(self._pdf_radio)
        fmt_layout.addStretch()
        layout.addLayout(fmt_layout)

        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Save to:"))
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Select output file path...")
        file_layout.addWidget(self._path_edit)
        self._save_btn = QPushButton("Browse...")
        file_layout.addWidget(self._save_btn)
        layout.addLayout(file_layout)

        self._save_btn.clicked.connect(self._on_browse)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_export)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_browse(self):
        if self._html_radio.isChecked():
            formats = "HTML Files (*.html *.htm)"
            ext = ".html"
        else:
            formats = "PDF Files (*.pdf)"
            ext = ".pdf"

        path, _ = QFileDialog.getSaveFileName(self, "Save Report", "", formats)
        if path:
            if not path.lower().endswith(ext):
                path += ext
            self._path_edit.setText(path)

    def _on_export(self):
        path = self._path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "Export", "Please select an output file path.")
            return

        try:
            html = _build_html(self._fonts, self._results)

            if self._pdf_radio.isChecked():
                self._save_pdf(html, path)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html)

            QMessageBox.information(self, "Export", f"Report saved to:\n{path}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _save_pdf(self, html: str, path: str):
        from PySide6.QtGui import QTextDocument
        from PySide6.QtPrintSupport import QPrinter

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)

        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)
