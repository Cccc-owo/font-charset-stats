# font-charset-stats

[English](README.md) | 中文

分析字体对中日韩编码标准及 Unicode 区块的字符集覆盖率 — 命令行与图形界面。

## 安装

```bash
# 仅命令行
pip install font-charset-stats

# 包含图形界面
pip install "font-charset-stats[gui]"
```

或使用 uv：

```bash
uv tool install font-charset-stats
```

## 使用

### 命令行

```bash
font-charset-stats /path/to/font.ttf
font-charset-stats /path/to/font.otf --format json
font-charset-stats --list                         # 列出可用字符集
font-charset-stats font.ttf --charsets GB2312,GBK --show-missing
```

输出格式：`text`（默认）、`json`、`csv`。

### 图形界面

```bash
font-charset-stats-gui
# 或
python -m font_charset_stats.gui
```

功能：

- 拖拽或浏览加载字体文件（.ttf、.otf、.woff、.woff2）
- 系统字体浏览器，支持字重过滤
- 多字体并排对比与分组柱状图
- 覆盖率表格，显示每字符集匹配数/总数
- 缺失码位浏览器，按 Unicode 区块分组
- 字体字形预览，TTC/OTC 支持变体选择
- 目录批量分析与 HTML/PDF 报告导出

## 支持的字符集

**编码标准：**
GB2312、GBK、GB18030（1–3 级）、GB12345、Big5、Big5-HKSCS、CNS11643、
JIS X 0208（1–2 级）、JIS X 0213、日语平假名/片假名、
KS X 1001 汉字、韩文谚文/字母

**CJK Unicode 区块：**
CJK 统一表意文字、扩展 A–I 区、兼容区、兼容补充区

**西方 Unicode 区块：**
基本拉丁字母、拉丁字母补充-1、拉丁字母扩展-A/B、国际音标扩展、
间距修饰符、组合变音符、希腊字母与科普特字母、西里尔字母、
常用标点、货币符号、箭头、数学运算符、
制表符、方块元素、几何图形、丁贝符等。

## 许可证

MIT — 详见 [LICENSE](LICENSE)。

内置图表字体 JetBrains Mono 采用 SIL Open Font License 许可。
