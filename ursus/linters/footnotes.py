from pathlib import Path
from ursus.linters import RegexLinter
import logging
import re


class OrphanFootnotesLinter(RegexLinter):
    """
    Count footnotes; make sure that they all appear at least twice
    """
    file_suffixes = '.md'
    regex = re.compile(r'.{0,15}(?P<footnote>\[\^(?P<key>\d+)\])(?P<colon>:?).{0,15}')

    def lint(self, file_path: Path):
        self.undefined_footnotes = {}
        unused_footnotes = list(super().lint(file_path))
        for key, uses in self.undefined_footnotes.items():
            for use in uses:
                yield 0, f"Undefined footnote: {use}", logging.ERROR
        yield from unused_footnotes

    def handle_match(self, file_path: Path, match: re.Match):
        if not match['colon']:  # Footnote reference
            self.undefined_footnotes.setdefault(match['key'], [])
            self.undefined_footnotes[match['key']].append(match.group(0))
        else:  # Footnote definition
            if match['key'] in self.undefined_footnotes:
                self.undefined_footnotes.pop(match['key'])
                pass
            else:
                yield f"Unused footnote: {match.group(0)}", logging.WARNING
