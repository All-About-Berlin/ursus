from pathlib import Path
from typing import Generator, Match
from ursus.config import config
import logging
import re


logger = logging.getLogger(__name__)


LinterResult = Generator[tuple[tuple[int, int, int] | None, str, int], None, None]
LineLinterResult = Generator[tuple[tuple[int, int] | None, str, int], None, None]
MatchResult = Generator[tuple[str, int], None, None]


class Linter():
    def lint(self, file_path: Path) -> LinterResult:
        """
        Lints the content for errors.
        """
        raise NotImplementedError


class LineLinter(Linter):
    """
    Lints a text file line by line.
    """
    file_suffixes: tuple[str, ...] = ()

    def lint(self, file_path: Path) -> LinterResult:
        if self.file_suffixes and file_path.suffix.lower() not in self.file_suffixes:
            return

        with (config.content_path / file_path).open() as file:
            for line_no, line in enumerate(file.readlines()):
                for col_range, error, level in self.lint_line(file_path, line):
                    yield (line_no, *col_range), error, level

    def lint_line(self, file_path: Path, line: str) -> LineLinterResult:
        raise NotImplementedError


class RegexLinter(LineLinter):
    regex = re.compile(r'')

    def lint_line(self, file_path: Path, line: str) -> LineLinterResult:
        for match in self.regex.finditer(line):
            for message, level in self.handle_match(file_path, match):
                yield match.span(), message, level

    def handle_match(self, file_path: Path, match: Match[str]) -> MatchResult:
        raise NotImplementedError
