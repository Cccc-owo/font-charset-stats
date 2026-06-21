"""Coverage analysis engine — matches font codepoints against charset definitions."""

from dataclasses import dataclass, field

from font_charset_stats.charsets.base import CharSet


def _is_control(cp: int) -> bool:
    return cp <= 0x1F or 0x7F <= cp <= 0x9F


@dataclass
class CoverageResult:
    name: str
    description: str
    total: int
    matched: int
    missing: list[int] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        if self.total == 0:
            return 1.0
        return self.matched / self.total

    @property
    def coverage_pct(self) -> str:
        return f"{self.coverage * 100:.2f}%"


def analyze(
    font_codepoints: set[int],
    charsets: list[CharSet],
    show_missing: bool = False,
    exclude_controls: bool = False,
) -> list[CoverageResult]:
    results: list[CoverageResult] = []

    font_cps = font_codepoints
    if exclude_controls:
        font_cps = {cp for cp in font_codepoints if not _is_control(cp)}

    for cs in charsets:
        cs_cps = cs.codepoints
        if exclude_controls:
            cs_cps = {cp for cp in cs.codepoints if not _is_control(cp)}

        matched = font_cps & cs_cps
        missing: list[int] = []
        if show_missing:
            missing = sorted(cs_cps - font_cps)

        results.append(
            CoverageResult(
                name=cs.name,
                description=cs.description,
                total=len(cs_cps),
                matched=len(matched),
                missing=missing,
            )
        )

    return results
