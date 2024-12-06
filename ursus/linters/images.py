from pathlib import Path
from ursus.config import config
from ursus.linters import Linter, LinterResult
from ursus.linters.markdown import MarkdownLinksLinter
from ursus.utils import is_image, get_files_in_path
import logging


class UnusedImagesLinter(Linter):
    """
    Verify that internal links point to existing entries. If the URL has a fragment,
    it should point to an existing title fragment.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_entry_links = set()

        link_regex = MarkdownLinksLinter.regex

        for markdown_path in get_files_in_path(config.content_path, suffix='.md'):
            with (config.content_path / markdown_path).open() as file:
                for line_no, line in enumerate(file.readlines()):
                    for match in link_regex.finditer(line):
                        entry_uri = match['url'].removeprefix('/')
                        self.all_entry_links.add(entry_uri)

    def lint(self, file_path: Path) -> LinterResult:
        if is_image(config.content_path / file_path) and str(file_path) not in self.all_entry_links:
            yield None, "Unused image", logging.WARNING
