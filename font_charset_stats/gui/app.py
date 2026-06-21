"""Main window and application entry point for font-charset-stats GUI."""

import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QThread, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from font_charset_stats.font_reader import FontInfo, probe_tc
from font_charset_stats.gui.charset_panel import CharsetPanel
from font_charset_stats.gui.font_list import FontListPanel
from font_charset_stats.gui.results_view import ResultsView
from font_charset_stats.gui.theme import apply_theme
from font_charset_stats.gui.worker import AnalysisWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Font Charset Stats")
        self.resize(1280, 800)

        self._fonts: list[FontInfo] = []
        self._last_results: list = []
        self._analyze_fonts_snapshot: list[FontInfo] = []
        self._analyze_charset_order: list[str] = []
        self._analyzing = False

        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)
        self._debounce.timeout.connect(self._on_auto_analyze)

        self._setup_worker()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_central()
        self._setup_statusbar()
        self._connect_signals()

    def _setup_worker(self):
        self._worker_thread = QThread()
        self._worker = AnalysisWorker()
        self._worker.moveToThread(self._worker_thread)

        self._worker.font_loaded.connect(self._on_font_loaded)
        self._worker.analysis_complete.connect(self._on_analysis_complete)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.progress.connect(self._on_progress)

        self._worker_thread.start()

    def _setup_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("&File")

        open_action = QAction("&Open Font...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_file)
        file_menu.addAction(open_action)

        batch_action = QAction("&Batch Analyze...", self)
        batch_action.setShortcut("Ctrl+B")
        batch_action.triggered.connect(self._on_batch)
        file_menu.addAction(batch_action)

        file_menu.addSeparator()

        export_action = QAction("&Export Report...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._on_export)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = menu.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        toolbar = self.addToolBar("Main")
        toolbar.setIconSize(QSize(16, 16))

        open_btn = QPushButton("Open Font")
        open_btn.clicked.connect(self._on_open_file)
        toolbar.addWidget(open_btn)

        batch_btn = QPushButton("Batch")
        batch_btn.clicked.connect(self._on_batch)
        toolbar.addWidget(batch_btn)

        toolbar.addSeparator()

        self._analyze_btn = QPushButton("Analyze")
        self._analyze_btn.clicked.connect(self._on_analyze)
        self._analyze_btn.setEnabled(False)
        toolbar.addWidget(self._analyze_btn)

        toolbar.addSeparator()

        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self._on_export)
        toolbar.addWidget(export_btn)

        toolbar.addSeparator()

        self._show_controls_cb = QCheckBox("Show Controls")
        self._show_controls_cb.setChecked(False)
        self._show_controls_cb.toggled.connect(self._on_show_controls_toggled)
        toolbar.addWidget(self._show_controls_cb)

    def _setup_central(self):
        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self._font_panel = FontListPanel()
        self._charset_panel = CharsetPanel()

        left_layout.addWidget(self._font_panel)
        left_layout.addWidget(self._charset_panel)

        self._results_view = ResultsView()

        splitter.addWidget(left_widget)
        splitter.addWidget(self._results_view)
        splitter.setSizes([400, 800])

        self.setCentralWidget(splitter)

    def _setup_statusbar(self):
        self.statusBar().showMessage("Ready")

    def _connect_signals(self):
        self._font_panel.font_added.connect(self._on_font_added)
        self._font_panel.fonts_changed.connect(self._on_fonts_changed)
        self._font_panel.variant_changed.connect(self._on_variant_changed)
        self._font_panel.system_fonts_requested.connect(self._on_system_fonts)
        self._charset_panel.selection_changed.connect(self._maybe_auto_analyze)

    def _on_open_file(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Open Font Files",
            "",
            "Font Files (*.ttf *.otf *.woff *.woff2);;All Files (*)",
        )
        for p in paths:
            self._font_panel.font_added.emit(p)

    def _on_font_added(self, path: str):
        self._load_font_path(path)

    def _on_font_loaded(self, font_info: FontInfo):
        variants = probe_tc(str(font_info.path))
        self._font_panel.add_font_info(font_info, variants if len(variants) > 1 else None)
        self._fonts.append(font_info)
        self.statusBar().showMessage(f"Loaded: {font_info.family_name or font_info.path.stem}")
        self._analyze_btn.setEnabled(True)
        self._debounce.start()

    def _on_variant_changed(self, font_index: int, font_number: int):
        font = self._font_panel.fonts()[font_index]
        self._font_panel.remove_font_at(font_index)
        self.statusBar().showMessage(f"Reloading: {font.path.name} face {font_number}...")
        self._worker.load_font(str(font.path), font_number=font_number)

    def _on_fonts_changed(self):
        self._fonts = self._font_panel.fonts()
        self._analyze_btn.setEnabled(len(self._fonts) > 0)
        if self._fonts:
            self._debounce.start()
        else:
            self._last_results = []
            self._results_view.set_results([], [])

    def _on_system_fonts(self):
        from font_charset_stats.gui.system_fonts_dialog import SystemFontsDialog

        dlg = SystemFontsDialog(self)
        dlg.font_selected.connect(lambda p, fi: self._load_font_path(p, fi))
        dlg.exec()

    def _load_font_path(self, path: str, face_index: int = 0):
        for font in self._font_panel.fonts():
            if str(font.path) == str(Path(path).resolve()):
                return
        self.statusBar().showMessage(f"Loading: {Path(path).name}...")
        self._worker.load_font(path, font_number=face_index)

    def _on_analyze(self):
        if self._analyzing:
            return
        fonts = self._font_panel.fonts()
        charsets = self._charset_panel.selected_charsets()
        if not fonts or not charsets:
            self.statusBar().showMessage("No fonts or charsets selected")
            return

        self._analyzing = True
        self._analyze_fonts_snapshot = list(fonts)
        self._analyze_charset_order = self._charset_panel.selected_names()
        self.statusBar().showMessage("Analyzing...")
        self._analyze_btn.setEnabled(False)
        self._worker.analyze_fonts(
            fonts,
            charsets,
            show_missing=True,
            exclude_controls=not self._show_controls_cb.isChecked(),
        )

    def _on_analysis_complete(self, results):
        self._analyzing = False
        self._last_results = results
        self._results_view.set_results(
            self._analyze_fonts_snapshot, results, self._analyze_charset_order
        )
        self._analyze_btn.setEnabled(True)
        self.statusBar().showMessage("Analysis complete")

    def _on_error(self, message: str):
        self.statusBar().showMessage(message)
        QMessageBox.warning(self, "Error", message)

    def _on_progress(self, completed: int, total: int):
        self.statusBar().showMessage(f"Analyzing... {completed}/{total}")

    def _on_auto_analyze(self):
        if self._analyzing:
            return
        if self._font_panel.fonts() and self._charset_panel.selected_charsets():
            self._on_analyze()

    def _maybe_auto_analyze(self):
        if self._analyzing:
            return
        if self._font_panel.fonts():
            self._debounce.start()

    def _on_show_controls_toggled(self):
        self._results_view.set_show_controls(self._show_controls_cb.isChecked())
        if self._font_panel.fonts() and self._charset_panel.selected_charsets():
            self._on_analyze()

    def _on_batch(self):
        from font_charset_stats.gui.batch_dialog import BatchDialog

        dlg = BatchDialog(self)
        dlg.exec()

    def _on_export(self):
        from font_charset_stats.gui.export_dialog import ExportDialog

        fonts = self._font_panel.fonts()
        if not self._last_results:
            self.statusBar().showMessage("No analysis results to export")
            return
        dlg = ExportDialog(fonts, self._last_results, self)
        dlg.exec()

    def _on_about(self):
        QMessageBox.about(
            self,
            "About Font Charset Stats",
            "font-charset-stats 0.1.0\n\n"
            "Analyze font character set coverage against\n"
            "Chinese / Japanese / Korean encoding standards.\n\n"
            "Powered by fonttools + PySide6",
        )

    def closeEvent(self, event):
        self._worker_thread.quit()
        self._worker_thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    apply_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
