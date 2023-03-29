from itertools import chain
from requests.exceptions import ConnectionError
from ursus.config import config
from ursus.linters import RegexLinter
import logging
import re
import requests


class MarkdownLinksLinter(RegexLinter):
    """
    Verifies external links in Markdown files
    """
    file_suffixes = ('.md',)

    # Matches [], supports escaped brackets, ignores ![] images.
    first_half = r"(?P<first_half>!?\[(?P<text>([^\]]|\\\])*)(?<!\\)\])"

    # Matches (), supports escaped parentheses
    second_half = r"(?P<second_half>\((?P<url_group>([^\)]|\\\))*)(?<!\\)\))"

    regex = re.compile(first_half + second_half)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_cache = {}

    def escape_url(self, url: str) -> str:
        return url.replace('(', '\\(').replace(')', '\\)')

    def unescape_url(self, url: str) -> str:
        return url.replace('\\(', '(').replace('\\)', ')')

    def validate_link_text(self, text: str, is_image: bool):
        return
        yield

    def validate_link_url(self, url: str, is_image: bool):
        return
        yield

    def validate_link_title(self, title: str, is_image: bool):
        return
        yield

    def handle_match(self, file: int, line: int, fix_errors: bool, match: re.Match):
        text = match['text'].strip()
        url = None
        title = None
        is_image = match['first_half'].startswith('!')

        if match['url_group']:
            parts = match['url_group'].split(" ", maxsplit=1)
            url = parts[0]
            if len(parts) == 2:
                title = parts[1]

        for error, level in chain(
            self.validate_link_text(text, is_image),
            self.validate_link_title(title, is_image),
            self.validate_link_url(url, is_image),
        ):
            self.log_error(file, line, f"{error}: {match.group(0)}", level)


class MarkdownLinkTextsLinter(MarkdownLinksLinter):
    def validate_link_text(self, text: str, is_image: bool):
        if not text:
            yield "Image has no alt text", logging.WARNING


class MarkdownLinkTitlesLinter(MarkdownLinksLinter):
    def validate_link_title(self, title: str, is_image: bool):
        if title is not None:
            if not (title.startswith('"') and title.endswith('"')):
                yield "Title is not quoted", logging.ERROR
            elif title == title.strip('"'):
                yield "Title is empty", logging.WARNING


class MarkdownExternalLinksLinter(MarkdownLinksLinter):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"

    def validate_link_url(self, url: str, is_image: bool):
        if not url:
            yield "Missing URL", logging.ERROR
        elif not url.startswith(('/', '#', 'http://', 'https://', 'mailto:', 'tel:')):
            yield "Relative or invalid URL", logging.WARNING
        else:
            if url.startswith(('http://', 'https://')):
                try:
                    cleaned_url = self.unescape_url(url)
                    if cleaned_url not in self.response_cache:
                        self.response_cache[cleaned_url] = requests.get(cleaned_url, timeout=5, headers={
                            'User-Agent': self.user_agent
                        })
                    response = self.response_cache[cleaned_url]
                    status_code = response.status_code
                except ConnectionError:
                    yield f"Connection error: {cleaned_url}", logging.ERROR
                except requests.exceptions.RequestException as exc:
                    yield f"URL {type(exc).__name__}: {cleaned_url}", logging.ERROR
                else:
                    if status_code in (404, 410):
                        yield f"URL returns HTTP {status_code}: {cleaned_url}", logging.ERROR
                    elif status_code >= 400:
                        severity = logging.WARNING if status_code in (403, 503) else logging.ERROR
                        yield f"URL returns HTTP {status_code}: {cleaned_url}", severity
                    elif response.history and response.history[-1].status_code == 301:
                        yield f"URL redirects to {response.url}", logging.INFO
