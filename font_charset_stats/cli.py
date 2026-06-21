"""CLI entry point for font-charset-stats."""

import argparse
import sys

from font_charset_stats import __version__
from font_charset_stats.analyzer import analyze
from font_charset_stats.charsets import ALL_CHARSETS, get_charset, list_charsets
from font_charset_stats.font_reader import read_font
from font_charset_stats.reporter import format_report


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="font-charset-stats",
        description="Analyze font character set coverage against CJK encoding standards.",
    )
    parser.add_argument(
        "font_path",
        nargs="?",
        default=None,
        help="Path to font file (.ttf, .otf, .woff, .woff2)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--charsets",
        "-c",
        help="Comma-separated list of charset names to analyze (default: all)",
    )
    parser.add_argument(
        "--show-missing",
        action="store_true",
        help="Show missing codepoints for each charset",
    )
    parser.add_argument(
        "--exclude-controls",
        action="store_true",
        help="Exclude control characters (U+0000-U+001F, U+007F-U+009F) from analysis",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Write output to file instead of stdout",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available charset names and exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"font-charset-stats {__version__}",
    )

    args = parser.parse_args()

    if args.list:
        print("Available charsets:")
        for name in list_charsets():
            cs = get_charset(name)
            print(f"  {name:25s} {cs.total:>10,d} cp  — {cs.description}")
        return

    if not args.font_path:
        parser.error("font_path is required unless --list is used")

    try:
        font_info = read_font(args.font_path)
    except Exception as e:
        print(f"Error reading font: {e}", file=sys.stderr)
        sys.exit(1)

    if args.charsets:
        names = [n.strip() for n in args.charsets.split(",") if n.strip()]
        try:
            charset_list = [get_charset(n) for n in names]
        except KeyError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        charset_list = [ALL_CHARSETS[n] for n in list_charsets()]

    results = analyze(
        font_info.codepoints,
        charset_list,
        show_missing=args.show_missing,
        exclude_controls=args.exclude_controls,
    )

    output = format_report(font_info, results, fmt=args.format, show_missing=args.show_missing)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
            f.write("\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
