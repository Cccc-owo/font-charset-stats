"""Batch analysis dialog for processing a directory of font files."""

from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from font_charset_stats.analyzer import CoverageResult, analyze
from font_charset_stats.charsets import ALL_CHARSETS, list_charsets
from font_charset_stats.font_reader import FontInfo, read_font
from font_charset_stats.gui import SUPPORTED_EXTS
from font_charset_stats.gui.theme import BATCH_COLORS


class BatchWorker(QObject):
    progress = Signal(int, int)
    font_done = Signal(str, object)
    font_error = Signal(str, str)
    finished = Signal(str)

    def __init__(self, font_files: list[Path], charset_list: list, parent=None):
        super().__init__(parent)
        self._font_files = font_files
        self._charset_list = charset_list

    def run(self) -> None:
        thread = QThread.currentThread()
        total = len(self._font_files)
        ok = 0

        for i, fp in enumerate(self._font_files):
            if thread.isInterruptionRequested():
                break
            try:
                font_info = read_font(str(fp))
                results = analyze(font_info.codepoints, self._charset_list)
                self.font_done.emit(str(fp), (font_info, results))
                ok += 1
            except Exception as e:
                self.font_error.emit(fp.name, str(e))
            self.progress.emit(i + 1, total)

        if thread.isInterruptionRequested():
            summary = self.tr("Cancelled")
        else:
            summary = self.tr("Done: %s/%s") % (ok, total)
        self.finished.emit(summary)


class BatchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: BatchWorker | None = None
        self._thread: QThread | None = None
        self._running = False

        self.setWindowTitle(self.tr("Batch Analyze"))
        self.resize(900, 500)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel(self.tr("Directory:")))
        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText(self.tr("Select a directory containing font files..."))
        dir_layout.addWidget(self._dir_edit)
        self._browse_btn = QPushButton(self.tr("Browse..."))
        dir_layout.addWidget(self._browse_btn)
        layout.addLayout(dir_layout)

        self._run_btn = QPushButton(self.tr("Run Batch Analysis"))
        layout.addWidget(self._run_btn)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status_label = QLabel()
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(
            [
                self.tr("Font"),
                self.tr("Best Coverage"),
                self.tr("Charset"),
                self.tr("Total Codepoints"),
            ]
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
        path = QFileDialog.getExistingDirectory(self, self.tr("Select Font Directory"))
        if path:
            self._dir_edit.setText(path)

    def _on_run(self):
        if self._running:
            self._cancel()
            return

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

        self._start_run(font_files)

    def _start_run(self, font_files: list[Path]):
        self._running = True
        self._run_btn.setText(self.tr("Cancel"))
        self._dir_edit.setEnabled(False)
        self._browse_btn.setEnabled(False)

        self._table.setRowCount(0)
        self._progress.setVisible(True)
        self._progress.setMaximum(len(font_files))
        self._progress.setValue(0)

        charset_list = [ALL_CHARSETS[n] for n in list_charsets()]

        self._thread = QThread()
        self._worker = BatchWorker(font_files, charset_list)
        self._worker.moveToThread(self._thread)

        self._worker.progress.connect(self._on_progress)
        self._worker.font_done.connect(self._on_font_done)
        self._worker.font_error.connect(self._on_font_error)
        self._worker.finished.connect(self._on_finished)
        self._thread.started.connect(self._worker.run)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._reset_ui)

        self._thread.start()

    def _cancel(self):
        if self._thread and self._thread.isRunning():
            self._thread.requestInterruption()
            self._run_btn.setEnabled(False)

    def _on_progress(self, completed: int, total: int):
        self._progress.setValue(completed)

    def _on_font_done(self, path: str, data: tuple[FontInfo, list[CoverageResult]]):
        font_info, results = data
        fp = Path(path)
        best = max(results, key=lambda r: r.coverage) if results else None

        row = self._table.rowCount()
        self._table.insertRow(row)

        name_item = QTableWidgetItem(font_info.family_name or fp.stem)
        name_item.setData(Qt.UserRole, path)
        self._table.setItem(row, 0, name_item)

        if best:
            pct_item = QTableWidgetItem(f"{best.coverage * 100:.1f}%")
            pct = best.coverage
            if pct >= 0.99:
                pct_item.setBackground(BATCH_COLORS["high"])
            elif pct >= 0.7:
                pct_item.setBackground(BATCH_COLORS["medium"])
            else:
                pct_item.setBackground(BATCH_COLORS["low"])
            self._table.setItem(row, 1, pct_item)
            self._table.setItem(row, 2, QTableWidgetItem(best.name))
        else:
            self._table.setItem(row, 1, QTableWidgetItem(self.tr("N/A")))
            self._table.setItem(row, 2, QTableWidgetItem("-"))

        self._table.setItem(row, 3, QTableWidgetItem(str(len(font_info.codepoints))))

    def _on_font_error(self, name: str, error_msg: str):
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(name))
        err_item = QTableWidgetItem(self.tr("Error: %s") % error_msg)
        err_item.setBackground(BATCH_COLORS["error"])
        self._table.setItem(row, 1, err_item)

    def _on_finished(self, summary: str):
        self._progress.setVisible(False)
        self._status_label.setText(summary)
        self._status_label.setVisible(True)

    def _reset_ui(self):
        self._running = False
        self._run_btn.setText(self.tr("Run Batch Analysis"))
        self._dir_edit.setEnabled(True)
        self._browse_btn.setEnabled(True)
        self._worker = None
        self._thread = None

    def _show_no_fonts(self):
        self._table.setRowCount(1)
        no_item = QTableWidgetItem(self.tr("No supported font files found in this directory"))
        no_item.setBackground(BATCH_COLORS["error"])
        self._table.setItem(0, 0, no_item)

    def reject(self):
        if self._running:
            self._cancel()
        super().reject()
