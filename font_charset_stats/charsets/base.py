from collections.abc import Callable


class CharSet:
    """Represents a character set standard with lazily-computed codepoints."""

    def __init__(self, name: str, description: str, builder: Callable[[], set[int]]):
        self.name = name
        self.description = description
        self._builder = builder
        self._codepoints: set[int] | None = None

    @property
    def codepoints(self) -> set[int]:
        if self._codepoints is None:
            self._codepoints = self._builder()
        return self._codepoints

    @property
    def total(self) -> int:
        return len(self.codepoints)

    def __repr__(self) -> str:
        return f"CharSet({self.name!r}, total={self.total})"
