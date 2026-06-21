"""Main window and application entry point for font-charset-stats GUI."""

import sys
from pathlib import Path
from typing import cast

from PySide6.QtCore import QEvent, QSize, Qt, QThread, QTimer
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
from font_charset_stats.gui.i18n import setup_translators, switch_language
from font_charset_stats.gui.results_view import ResultsView
from font_charset_stats.gui.theme import apply_theme
from font_charset_stats.gui.worker import AnalysisWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("Font Charset Stats"))
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
        menu.clear()

        self._file_menu = menu.addMenu(self.tr("&File"))

        self._open_action = QAction(self.tr("&Open Font..."), self)
        self._open_action.setShortcut("Ctrl+O")
        self._open_action.triggered.connect(self._on_open_file)
        self._file_menu.addAction(self._open_action)

        self._batch_action = QAction(self.tr("&Batch Analyze..."), self)
        self._batch_action.setShortcut("Ctrl+B")
        self._batch_action.triggered.connect(self._on_batch)
        self._file_menu.addAction(self._batch_action)

        self._file_menu.addSeparator()

        self._export_action = QAction(self.tr("&Export Report..."), self)
        self._export_action.setShortcut("Ctrl+E")
        self._export_action.triggered.connect(self._on_export)
        self._file_menu.addAction(self._export_action)

        self._file_menu.addSeparator()

        self._quit_action = QAction(self.tr("&Quit"), self)
        self._quit_action.setShortcut("Ctrl+Q")
        self._quit_action.triggered.connect(self.close)
        self._file_menu.addAction(self._quit_action)

        self._lang_menu = menu.addMenu(self.tr("&Language"))
        en_action = QAction("English", self)
        en_action.triggered.connect(
            lambda: switch_language(cast(QApplication, QApplication.instance()), "")
        )
        self._lang_menu.addAction(en_action)
        zh_action = QAction("中文", self)
        zh_action.triggered.connect(
            lambda: switch_language(cast(QApplication, QApplication.instance()), "zh_CN")
        )
        self._lang_menu.addAction(zh_action)

        self._help_menu = menu.addMenu(self.tr("&Help"))
        self._about_action = QAction(self.tr("&About"), self)
        self._about_action.triggered.connect(self._on_about)
        self._help_menu.addAction(self._about_action)
        self._license_action = QAction(self.tr("&License"), self)
        self._license_action.triggered.connect(self._on_license)
        self._help_menu.addAction(self._license_action)

    def _setup_toolbar(self):
        toolbar = self.addToolBar("Main")
        toolbar.setIconSize(QSize(16, 16))

        self._open_btn = QPushButton(self.tr("Open Font"))
        self._open_btn.clicked.connect(self._on_open_file)
        toolbar.addWidget(self._open_btn)

        self._batch_btn = QPushButton(self.tr("Batch"))
        self._batch_btn.clicked.connect(self._on_batch)
        toolbar.addWidget(self._batch_btn)

        toolbar.addSeparator()

        self._analyze_btn = QPushButton(self.tr("Analyze"))
        self._analyze_btn.clicked.connect(self._on_analyze)
        self._analyze_btn.setEnabled(False)
        toolbar.addWidget(self._analyze_btn)

        toolbar.addSeparator()

        self._export_btn = QPushButton(self.tr("Export"))
        self._export_btn.clicked.connect(self._on_export)
        toolbar.addWidget(self._export_btn)

        toolbar.addSeparator()

        self._show_controls_cb = QCheckBox(self.tr("Show Controls"))
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
        self.statusBar().showMessage(self.tr("Ready"))

    def _connect_signals(self):
        self._font_panel.font_added.connect(self._on_font_added)
        self._font_panel.fonts_changed.connect(self._on_fonts_changed)
        self._font_panel.variant_changed.connect(self._on_variant_changed)
        self._font_panel.system_fonts_requested.connect(self._on_system_fonts)
        self._charset_panel.selection_changed.connect(self._maybe_auto_analyze)

    def _on_open_file(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("Open Font Files"),
            "",
            self.tr("Font Files (*.ttf *.otf *.woff *.woff2);;All Files (*)"),
        )
        for p in paths:
            self._font_panel.font_added.emit(p)

    def _on_font_added(self, path: str):
        self._load_font_path(path)

    def _on_font_loaded(self, font_info: FontInfo):
        variants = probe_tc(str(font_info.path))
        self._font_panel.add_font_info(font_info, variants if len(variants) > 1 else None)
        self._fonts.append(font_info)
        name = font_info.family_name or font_info.path.stem
        self.statusBar().showMessage(self.tr("Loaded: %s") % name)
        self._analyze_btn.setEnabled(True)
        self._debounce.start()

    def _on_variant_changed(self, font_index: int, font_number: int):
        font = self._font_panel.fonts()[font_index]
        self._font_panel.remove_font_at(font_index)
        msg = self.tr("Reloading: %s face %s...") % (font.path.name, font_number)
        self.statusBar().showMessage(msg)
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
        self.statusBar().showMessage(self.tr("Loading: %s...") % Path(path).name)
        self._worker.load_font(path, font_number=face_index)

    def _on_analyze(self):
        if self._analyzing:
            return
        fonts = self._font_panel.fonts()
        charsets = self._charset_panel.selected_charsets()
        if not fonts or not charsets:
            self.statusBar().showMessage(self.tr("No fonts or charsets selected"))
            return

        self._analyzing = True
        self._analyze_fonts_snapshot = list(fonts)
        self._analyze_charset_order = self._charset_panel.selected_names()
        self.statusBar().showMessage(self.tr("Analyzing..."))
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
        self.statusBar().showMessage(self.tr("Analysis complete"))

    def _on_error(self, message: str):
        self.statusBar().showMessage(message)
        QMessageBox.warning(self, self.tr("Error"), message)

    def _on_progress(self, completed: int, total: int):
        self.statusBar().showMessage(self.tr("Analyzing... %s/%s") % (completed, total))

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
            self.statusBar().showMessage(self.tr("No analysis results to export"))
            return
        dlg = ExportDialog(fonts, self._last_results, self)
        dlg.exec()

    def _on_about(self):
        QMessageBox.about(
            self,
            self.tr("About Font Charset Stats"),
            "font-charset-stats 0.1.0\n\n"
            + self.tr(
                "Analyze font character set coverage against\n"
                "Chinese / Japanese / Korean encoding standards.\n\n"
                "Copyright (c) 2026 Cccc_\n"
                "Licensed under the MIT License.\n\n"
                "Powered by fonttools + PySide6"
            ),
        )

    def _on_license(self):
        QMessageBox.information(
            self,
            self.tr("MIT License"),
            "font-charset-stats 0.1.0\n"
            "Copyright (c) 2026 Cccc_\n\n"
            "Permission is hereby granted, free of charge, to any person "
            "obtaining a copy of this software and associated documentation "
            'files (the "Software"), to deal in the Software without '
            "restriction, including without limitation the rights to use, "
            "copy, modify, merge, publish, distribute, sublicense, and/or "
            "sell copies of the Software, and to permit persons to whom "
            "the Software is furnished to do so, subject to the following "
            "conditions:\n\n"
            "The above copyright notice and this permission notice shall "
            "be included in all copies or substantial portions of the "
            "Software.\n\n"
            'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY '
            "KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE "
            "WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR "
            "PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS "
            "OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR "
            "OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR "
            "OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE "
            "SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.",
        )

    def changeEvent(self, event):
        if event.type() == QEvent.Type.LanguageChange:
            self._retranslate()
        super().changeEvent(event)

    def _retranslate(self):
        self.setWindowTitle(self.tr("Font Charset Stats"))
        self._file_menu.setTitle(self.tr("&File"))
        self._open_action.setText(self.tr("&Open Font..."))
        self._batch_action.setText(self.tr("&Batch Analyze..."))
        self._export_action.setText(self.tr("&Export Report..."))
        self._quit_action.setText(self.tr("&Quit"))
        self._lang_menu.setTitle(self.tr("&Language"))
        self._help_menu.setTitle(self.tr("&Help"))
        self._about_action.setText(self.tr("&About"))
        self._license_action.setText(self.tr("&License"))
        self._open_btn.setText(self.tr("Open Font"))
        self._batch_btn.setText(self.tr("Batch"))
        self._analyze_btn.setText(self.tr("Analyze"))
        self._export_btn.setText(self.tr("Export"))
        self._show_controls_cb.setText(self.tr("Show Controls"))
        self._font_panel.retranslate()
        self._charset_panel.retranslate()
        self._results_view.retranslate()

    def closeEvent(self, event):
        self._worker_thread.quit()
        self._worker_thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    apply_theme(app)
    setup_translators(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
