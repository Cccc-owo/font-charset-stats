"""Unified entry point for the standalone executable.

- No arguments or --gui → launch GUI
- Any other arguments → run CLI
"""

import sys


def main() -> None:
    if len(sys.argv) <= 1 or sys.argv[1] == "--gui":
        from font_charset_stats.gui.app import main as gui_main

        gui_main()
    else:
        from font_charset_stats.cli import main as cli_main

        cli_main()


if __name__ == "__main__":
    main()
