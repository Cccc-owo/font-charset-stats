"""Coverage analysis engine — matches font codepoints against charset definitions."""

from dataclasses import dataclass, field

from font_charset_stats.charsets.base import CharSet


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
) -> list[CoverageResult]:
    results: list[CoverageResult] = []

    for cs in charsets:
        matched = font_codepoints & cs.codepoints
        missing: list[int] = []
        if show_missing:
            missing = sorted(cs.codepoints - font_codepoints)

        results.append(
            CoverageResult(
                name=cs.name,
                description=cs.description,
                total=cs.total,
                matched=len(matched),
                missing=missing,
            )
        )

    return results
