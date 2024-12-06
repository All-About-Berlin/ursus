from pathlib import Path
from ursus.config import config
from ursus.linters import RegexLinter, LinterResult
import logging
import re


class OrphanFootnotesLinter(RegexLinter):
    """
    Count footnotes; make sure that they all appear at least twice
    """
    file_suffixes = ('.md', )
    regex = re.compile(r'(?P<footnote>\[\^(?P<id>\d+)\])(?P<colon>:?)')

    def lint(self, file_path: Path) -> LinterResult:
        if self.file_suffixes and file_path.suffix.lower() not in self.file_suffixes:
            return

        footnotes: dict[str, list[dict]] = {}

        with (config.content_path / file_path).open() as file:
            for line_no, line in enumerate(file.readlines()):
                for match in self.regex.finditer(line):
                    footnotes.setdefault(match['id'], [])
                    footnotes[match['id']].append({
                        'position': (line_no, *match.span()),
                        'is_definition': bool(match['colon']),
                    })

        for footnote_id, occurences in footnotes.items():
            definitions = [o for o in occurences if o['is_definition']]

            if len(definitions) == 0:
                for occurence in occurences:
                    yield occurence['position'], f"Undefined footnote: [^{footnote_id}]", logging.ERROR
            elif len(definitions) > 1:
                for definition in definitions:
                    yield definition['position'], f"Multiple footnote definitions: [^{footnote_id}]", logging.ERROR
            elif len(definitions) == len(occurences):
                for occurence in occurences:
                    yield occurence['position'], f"Unused footnote: [^{footnote_id}]", logging.ERROR
