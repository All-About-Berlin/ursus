from pathlib import Path
from ursus.config import config
import logging
import re


logger = logging.getLogger(__name__)


class Linter():
    def lint(self, file_path: Path):
        """
        Lints the content for errors.
        """
        raise NotImplementedError


class LineLinter(Linter):
    """
    Lints a text file line by line.
    """
    file_suffixes = None

    def lint(self, file_path: Path):
        if self.file_suffixes and file_path.suffix.lower() not in self.file_suffixes:
            return

        with (config.content_path / file_path).open() as file:
            for line_no, line in enumerate(file.readlines()):
                for error, level in self.lint_line(file_path, line):
                    yield line_no, error, level

    def lint_line(self, file_path: Path, line: str):
        raise NotImplementedError


class RegexLinter(LineLinter):
    regex = re.compile(r'')

    def lint_line(self, file_path: Path, line: str):
        for match in self.regex.finditer(line):
            yield from self.handle_match(file_path, match)

    def handle_match(self, file_path: Path, match: re.Match):
        raise NotImplementedError
