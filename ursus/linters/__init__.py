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


class RegexLinter(Linter):
    file_suffixes = None
    regex = re.compile(r'')

    def lint(self, file_path: Path):
        if self.file_suffixes and file_path.suffix.lower() not in self.file_suffixes:
            return

        with (config.content_path / file_path).open() as file:
            for line_no, line in enumerate(file.readlines()):
                for match in self.regex.finditer(line):
                    for error, level in self.handle_match(file_path, match):
                        yield line_no, error, level

    def handle_match(self, file_path: Path, match: re.Match):
        raise NotImplementedError
