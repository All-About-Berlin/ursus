from itertools import chain
from markdown.blockprocessors import HashHeaderProcessor
from pathlib import Path
from requests.exceptions import ConnectionError
from urllib.parse import unquote, urlparse
from ursus.config import config
from ursus.context_processors.markdown import patched_slugify
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

    def handle_match(self, file_path: Path, match: re.Match):
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
            self.validate_link_text(text, is_image, file_path),
            self.validate_link_title(title, is_image, file_path),
            self.validate_link_url(url, is_image, file_path),
        ):
            yield f"{error}: {match.group(0)}", level

    def validate_link_text(self, text: str, is_image: bool, file_path: Path):
        return
        yield

    def validate_link_url(self, url: str, is_image: bool, file_path: Path):
        return
        yield

    def validate_link_title(self, title: str, is_image: bool, file_path: Path):
        return
        yield


class MarkdownLinkTextsLinter(MarkdownLinksLinter):
    def validate_link_text(self, text: str, is_image: bool, file_path: Path):
        if not text:
            yield "Image has no alt text", logging.WARNING


class MarkdownLinkTitlesLinter(MarkdownLinksLinter):
    def validate_link_title(self, title: str, is_image: bool, file_path: Path):
        if title is not None:
            if not (title.startswith('"') and title.endswith('"')):
                yield "Title is not quoted", logging.ERROR
            elif title == title.strip('"'):
                yield "Title is empty", logging.WARNING


class MarkdownExternalLinksLinter(MarkdownLinksLinter):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_cache = {}

    def validate_link_url(self, url: str, is_image: bool, file_path: Path):
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
                        yield f"URL returns HTTP {status_code}", logging.ERROR
                    elif status_code >= 400:
                        level = logging.WARNING if status_code in (403, 503) else logging.ERROR
                        yield f"URL returns HTTP {status_code}", level
                    elif response.history and response.history[-1].status_code == 301:
                        yield f"URL redirects to {response.url}", logging.INFO

    def escape_url(self, url: str) -> str:
        return url.replace('(', '\\(').replace(')', '\\)')

    def unescape_url(self, url: str) -> str:
        return url.replace('\\(', '(').replace('\\)', ')')


class MarkdownInternalLinksLinter(MarkdownLinksLinter):
    """
    Verify that internal links point to existing entries. If the URL has a fragment,
    it should point to an existing title fragment.
    """
    header_regex = HashHeaderProcessor.RE
    ignored_urls = (
        # re.compile(r'^/ignored-url$')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title_slugs_cache = {}

    def get_title_slugs(self, file_path: Path):
        if file_path not in self.title_slugs_cache:
            self.title_slugs_cache[file_path] = set()
            with file_path.open() as file:
                for line in file.readlines():
                    if bool(self.header_regex.search(line)):
                        self.title_slugs_cache[file_path].add(
                            patched_slugify(line.lstrip('#').strip(), '-')
                        )
        return self.title_slugs_cache[file_path]

    def validate_link_url(self, url: str, is_image: bool, current_file_path: Path):
        for ignored_url in self.ignored_urls:
            if ignored_url.match(url):
                return

        url_parts = urlparse(url)
        title_slug = url_parts.fragment

        # Convert relative and absolute URLs to content paths
        if config.site_url and url.startswith(config.site_url):
            file_path = config.content_path / unquote(url_parts.path.removeprefix(config.site_url))
        elif url.startswith('/'):
            file_path = config.content_path / unquote(url_parts.path.lstrip('/'))
        elif url.startswith('#'):
            file_path = config.content_path / current_file_path
        elif not url_parts.scheme and not url_parts.netloc:  # Relative URL
            file_path = current_file_path.parent / unquote(url_parts.path)
        else:
            return

        if file_path.suffix.lower() == config.html_url_extension:
            file_path = file_path.with_suffix('.md')

        if not file_path.exists():
            yield "Entry not found", logging.ERROR
        elif title_slug and title_slug not in self.get_title_slugs(file_path):
            yield "URL fragment not found", logging.ERROR
