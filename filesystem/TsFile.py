from typing import Callable


class TsFile:
    def __init__(self, hash: int, read_func: Callable[[], bytes]):
        self.hash = hash
        self._read_func = read_func

        self.path: str | None = None
        self.underlying_paths: list[str] = []

    def read(self) -> bytes:
        return self._read_func()
