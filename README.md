# font-charset-stats

English | [中文](README_zh-CN.md)

Analyze font character set coverage against CJK encoding standards and Unicode blocks — CLI and GUI.

## Installation

```bash
# CLI only
pip install font-charset-stats

# With GUI
pip install "font-charset-stats[gui]"
```

Or with uv:

```bash
uv tool install font-charset-stats
```

## Usage

### CLI

```bash
font-charset-stats /path/to/font.ttf
font-charset-stats /path/to/font.otf --format json
font-charset-stats --list                         # list available charsets
font-charset-stats font.ttf --charsets GB2312,GBK --show-missing
```

Output formats: `text` (default), `json`, `csv`.

### GUI

```bash
font-charset-stats-gui
# or
python -m font_charset_stats.gui
```

Features:

- Drag-and-drop or browse font files (.ttf, .otf, .woff, .woff2)
- System font browser with weight filtering
- Multi-font side-by-side comparison with grouped bar charts
- Coverage table with per-charset matched/total counts
- Missing codepoint explorer grouped by Unicode block
- Font glyph preview with variant selection for TTC/OTC collections
- Batch directory analysis and HTML/PDF export

## Supported Charsets

**Encoding standards:**
GB2312, GBK, GB18030 (Level 1–3), GB12345, Big5, Big5-HKSCS, CNS11643,
JIS X 0208 (Level 1–2), JIS X 0213, Japanese Hiragana/Katakana,
KS X 1001 Hanja, Korean Hangul/Jamo

**CJK Unicode blocks:**
CJK Unified Ideographs, Extensions A–I, Compatibility, Compatibility Supplement

**Western Unicode blocks:**
Basic Latin, Latin-1 Supplement, Latin Extended-A/B, IPA Extensions,
Spacing Modifier, Combining Diacritical, Greek and Coptic, Cyrillic,
General Punctuation, Currency Symbols, Arrows, Mathematical Operators,
Box Drawing, Geometric Shapes, Dingbats, and more.

## License

[MIT](LICENSE).

JetBrains Mono (bundled chart font) is licensed under the SIL Open Font License.
