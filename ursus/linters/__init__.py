from functools import partial
from pathlib import Path
from ursus.config import config
import logging
import re


logger = logging.getLogger(__name__)


class Linter():
    def lint(self, file_path: Path, fix_errors: bool = False):
        """
        Lints the content for errors.
        """
        raise NotImplementedError

    def log_error(self, file_path: int, line_no: int, message: str, level=logging.WARNING):
        color = {
            logging.DEBUG: '',
            logging.INFO: '\033[37m\033[0;100m',
            logging.WARNING: '\033[1;90m\033[43m',
            logging.ERROR: '\033[37m\033[41m',
            logging.CRITICAL: '\033[37m\033[41m',
        }[level]
        if line_no:
            logger.log(level, f"    {color}:{line_no}\033[0m {message}")
        else:
            logger.log(level, f"    {message}")

    def log_substitution(self, file_path: int, line_no: int, old: str, new: str):
        logger.info(f"      \033[0;31m- {old}\033[0m")
        logger.info(f"      \033[0;32m+ {new}\033[0m")


class RegexLinter(Linter):
    file_suffixes = None
    regex = re.compile(r'')

    def lint(self, file_path: Path, fix_errors: bool = False):
        if not self.file_suffixes or file_path.suffix in self.file_suffixes:
            with (config.content_path / file_path).open() as file:
                for line_no, line in enumerate(file.readlines()):
                    sub_func = partial(self.handle_match, file_path, line_no, fix_errors)
                    self.regex.sub(sub_func, line)

    def handle_match(self, file_path: int, line_no: int, fix_errors: bool, match: re.Match):
        raise NotImplementedError
