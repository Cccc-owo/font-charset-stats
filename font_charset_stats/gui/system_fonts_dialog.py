"""Dialog for browsing and loading system-installed fonts."""

import contextlib
import io
import os
import platform
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QVBoxLayout,
)

_FC_WEIGHT_REGULAR = 80


def _find_system_fonts() -> list[tuple[str, str, int, int]]:
    """Return list of (family_name, file_path, face_index, weight_class)."""
    system = platform.system()

    if system == "Linux":
        try:
            result = subprocess.run(
                [
                    "fc-list",
                    "--format=%{family[0]}\x1f%{file}\x1f%{index}\x1f%{weight}\n",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                pairs: list[tuple[str, str, int, int]] = []
                for line in result.stdout.strip().split("\n"):
                    parts = line.split("\x1f")
                    if len(parts) >= 4:
                        family = parts[0].strip()
                        filepath = parts[1].strip()
                        try:
                            index = int(parts[2].strip())
                        except ValueError:
                            index = 0
                        try:
                            weight = int(float(parts[3].strip()))
                        except ValueError:
                            weight = 400
                        if family and filepath:
                            pairs.append((family, filepath, index, weight))
                return pairs
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    font_dirs: list[Path] = []
    if system == "Linux":
        font_dirs = [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".fonts",
            Path.home() / ".local/share/fonts",
        ]
    elif system == "Darwin":
        font_dirs = [
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            Path.home() / "Library/Fonts",
        ]
    elif system == "Windows":
        windir = Path(os.environ.get("SYSTEMROOT", r"C:\Windows"))
        font_dirs = [windir / "Fonts"]

    pairs: list[tuple[str, str, int, int]] = []
    for d in font_dirs:
        if not d.is_dir():
            continue
        for fp in d.rglob("*"):
            if fp.suffix.lower() not in (".ttf", ".otf", ".ttc", ".woff", ".woff2"):
                continue
            try:
                from fontTools.ttLib import TTFont

                font = TTFont(fp, fontNumber=0)
                name = ""
                weight = 400
                name_table = font.get("name")
                if name_table:
                    for record in name_table.names:
                        if record.nameID == 1:
                            with contextlib.suppress(UnicodeDecodeError, AttributeError):
                                name = record.toUnicode()
                            break
                os2 = font.get("OS/2")
                if os2:
                    weight = getattr(os2, "usWeightClass", 400) * 80 // 400
                pairs.append((name or fp.stem, str(fp), 0, weight))
                font.close()
            except Exception:
                pass
    return pairs


class _ScanWorker(QThread):
    finished_scan = Signal(list)
    error_scan = Signal(str)

    def run(self):
        try:
            result = _find_system_fonts()
            self.finished_scan.emit(result)
        except Exception as e:
            self.error_scan.emit(str(e))


class SystemFontsDialog(QDialog):
    font_selected = Signal(str, int)  # path, face_index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("System Fonts"))
        self.resize(650, 500)
        self._fonts: list[tuple[str, str, int, int]] = []

        self._setup_ui()
        self._start_scan()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._filter = QLineEdit()
        self._filter.setPlaceholderText(self.tr("Filter by family name..."))
        layout.addWidget(self._filter)

        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(800)
        self._filter_timer.timeout.connect(self._do_filter)
        self._filter.textChanged.connect(self._on_filter_changed)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        layout.addWidget(self._progress)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_accept)
        layout.addWidget(self._list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _start_scan(self):
        self._worker = _ScanWorker()
        self._worker.finished_scan.connect(self._on_scan_done)
        self._worker.error_scan.connect(self._on_scan_error)
        self._worker.start()

    def _on_scan_done(self, fonts: list[tuple[str, str, int, int]]):
        self._progress.setVisible(False)
        self._fonts = sorted(fonts, key=lambda x: (x[0].lower(), x[1]))

        best: dict[str, tuple[str, str, int, int]] = {}
        for family, filepath, face_idx, weight in self._fonts:
            key = family.lower()
            prev = best.get(key)
            if prev is None or abs(weight - _FC_WEIGHT_REGULAR) < abs(prev[3] - _FC_WEIGHT_REGULAR):
                best[key] = (family, filepath, face_idx, weight)

        with contextlib.redirect_stderr(io.StringIO()):
            for key in sorted(best):
                display_name, filepath, face_idx, _weight = best[key]
                item = QListWidgetItem(display_name)
                item.setData(Qt.ItemDataRole.UserRole, filepath)
                item.setData(Qt.ItemDataRole.UserRole + 1, face_idx)
                item.setFont(QFont(display_name, 12))
                self._list.addItem(item)

        self._filter.setFocus()

    def _on_scan_error(self, msg: str):
        self._progress.setVisible(False)
        QMessageBox.warning(self, "Scan Error", msg)

    def _on_filter_changed(self):
        self._filter_timer.start()

    def _do_filter(self):
        text = self._filter.text()
        lower = text.lower()
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item:
                item.setHidden(bool(lower and lower not in (item.text().lower() or "")))

    def _on_accept(self):
        items = self._list.selectedItems()
        if not items:
            return
        for item in items:
            path = item.data(Qt.ItemDataRole.UserRole)
            face_idx = item.data(Qt.ItemDataRole.UserRole + 1)
            if path:
                self.font_selected.emit(path, face_idx or 0)
        self.accept()
