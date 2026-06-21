"""Theme configuration for font-charset-stats GUI."""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def _dark_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.Window, QColor(53, 53, 53))
    p.setColor(QPalette.WindowText, QColor(255, 255, 255))
    p.setColor(QPalette.Base, QColor(35, 35, 35))
    p.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    p.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
    p.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    p.setColor(QPalette.Text, QColor(255, 255, 255))
    p.setColor(QPalette.Button, QColor(53, 53, 53))
    p.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    p.setColor(QPalette.BrightText, QColor(255, 0, 0))
    p.setColor(QPalette.Link, QColor(42, 130, 218))
    p.setColor(QPalette.Highlight, QColor(42, 130, 218))
    p.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    p.setColor(QPalette.Disabled, QPalette.WindowText, QColor(128, 128, 128))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor(128, 128, 128))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(128, 128, 128))
    return p


def apply_theme(app: QApplication) -> None:
    """Apply Fusion style with a dark palette."""
    app.setStyle("Fusion")
    app.setPalette(_dark_palette())


# -- Coverage heatmap colors (BackgroundRole per cell) ------------------

_COVERAGE_PALETTE: list[tuple[float, QColor]] = [
    (0.99, QColor(70, 140, 80)),
    (0.90, QColor(130, 150, 60)),
    (0.70, QColor(180, 150, 50)),
    (0.50, QColor(190, 120, 50)),
    (0.00, QColor(190, 80, 70)),
]

COVERAGE_FG = QColor(255, 255, 255)


def coverage_bg_color(pct: float) -> QColor:
    """Return a background color for the given coverage percentage."""
    for threshold, color in _COVERAGE_PALETTE:
        if pct >= threshold:
            return color
    return _COVERAGE_PALETTE[-1][1]  # pragma: no cover


# -- Batch dialog cell colors -------------------------------------------

BATCH_COLORS: dict[str, QColor] = {
    "high": QColor(70, 140, 80),
    "medium": QColor(180, 150, 50),
    "low": QColor(190, 80, 70),
    "error": QColor(130, 90, 60),
}


# -- Matplotlib chart colors --------------------------------------------

CHART_COLORS: list[str] = [
    "#60a5fa",
    "#f87171",
    "#4ade80",
    "#c084fc",
    "#818cf8",
    "#fbbf24",
    "#34d399",
    "#f472b6",
]

CHART_TEXT_COLOR = "#333"
