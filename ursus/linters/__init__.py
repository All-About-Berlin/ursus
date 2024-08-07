from markdown.extensions.meta import META_RE, BEGIN_RE, END_RE, META_MORE_RE
from pathlib import Path
from typing import Any
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
                for col_range, error, level in self.lint_line(file_path, line):
                    yield (line_no, *col_range), error, level

    def lint_line(self, file_path: Path, line: str):
        raise NotImplementedError


class RegexLinter(LineLinter):
    regex = re.compile(r'')

    def lint_line(self, file_path: Path, line: str):
        for match in self.regex.finditer(line):
            for message, level in self.handle_match(file_path, match):
                yield match.span(), message, level

    def handle_match(self, file_path: Path, match: re.Match):
        raise NotImplementedError


class HeadMatterLinter(Linter):
    def lint(self, file_path: Path):
        if file_path.suffix.lower() != '.md':
            return

        meta: dict[str, Any] = {}
        field_positions: dict[str, tuple] = {}

        with (config.content_path / file_path).open() as file:
            lines = file.readlines()

        if lines and BEGIN_RE.match(lines[0]):
            lines.pop(0)

        for line_no, line in enumerate(lines):
            m1 = META_RE.match(line)
            if line.strip() == '' or END_RE.match(line):
                break  # blank line or end of YAML header - done
            if m1:
                key = m1.group('key').lower().strip()
                value = m1.group('value').strip()
                try:
                    meta[key].append(value)
                except KeyError:
                    meta[key] = [value]
                field_positions[key] = (line_no + 1, 0, len(line) - 1)
            else:
                m2 = META_MORE_RE.match(line)
                if m2 and key:
                    # Add another line to existing key
                    meta[key].append(m2.group('value').strip())
                else:
                    lines.insert(0, line)
                    break
        yield from self.lint_meta(meta, field_positions)

    def lint_meta(self, meta: dict[str, Any], field_positions: dict[str, tuple]):
        raise NotImplementedError
