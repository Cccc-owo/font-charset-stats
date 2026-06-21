"""Background worker for non-blocking font analysis."""

from PySide6.QtCore import QObject, Signal

from font_charset_stats.analyzer import CoverageResult, analyze
from font_charset_stats.charsets.base import CharSet
from font_charset_stats.font_reader import FontInfo, read_font


class AnalysisWorker(QObject):
    """Runs font I/O and coverage analysis in a background thread."""

    font_loaded = Signal(FontInfo)
    analysis_complete = Signal(list)
    error_occurred = Signal(str)
    progress = Signal(int, int)

    def load_font(self, path: str, font_number: int = 0):
        try:
            font_info = read_font(path, font_number=font_number)
            self.font_loaded.emit(font_info)
        except Exception as e:
            self.error_occurred.emit(f"Failed to load font: {e}")

    def analyze_fonts(
        self,
        fonts: list[FontInfo],
        charsets: list[CharSet],
        show_missing: bool = False,
        exclude_controls: bool = False,
    ):
        results: list[CoverageResult] = []
        total = len(fonts) * len(charsets)
        completed = 0
        try:
            for font in fonts:
                font_results = analyze(
                    font.codepoints,
                    charsets,
                    show_missing=show_missing,
                    exclude_controls=exclude_controls,
                )
                results.extend(font_results)
                completed += len(charsets)
                self.progress.emit(completed, total)
            self.analysis_complete.emit(results)
        except Exception as e:
            self.error_occurred.emit(f"Analysis failed: {e}")
