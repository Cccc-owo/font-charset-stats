"""Build standalone executable with Nuitka.

Produces a single .exe with UPX compression.  Supports CLI mode:
    FontCharsetStats.exe                -> GUI
    FontCharsetStats.exe --help          -> CLI
    FontCharsetStats.exe font.ttf        -> CLI
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build():
    args = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--onefile",
        "--windows-console-mode=attach",
        "--enable-plugin=pyside6",
        "--include-package-data=font_charset_stats",
        "--include-data-dir=font_charset_stats/charsets/data=charsets/data",
        "--include-data-dir=font_charset_stats/gui/fonts=gui/fonts",
        "--include-data-dir=font_charset_stats/gui/i18n=gui/i18n",
        "--output-dir=dist",
        "--output-filename=FontCharsetStats",
        "--assume-yes-for-downloads",
        str(ROOT / "font_charset_stats" / "run.py"),
    ]
    subprocess.run(args, check=True, cwd=str(ROOT))


if __name__ == "__main__":
    build()
