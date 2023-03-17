from requests.exceptions import ConnectionError
from ursus.config import config
from ursus.linters import RegexLinter
import logging
import re
import requests


class MarkdownLinksLinter(RegexLinter):
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

    def handle_match(self, file: int, line: int, fix_errors: bool, match: re.Match):
        original_text = match.group(0)
        new_text = original_text
        text = match['text'].strip()
        url = None
        title = None
        is_image = match['first_half'].startswith('!')

        if match['url_group']:
            parts = match['url_group'].split(" ", maxsplit=1)
            url = parts[0]
            if len(parts) == 2:
                title = parts[1]

        # Validate the link text
        if text in ('click', 'here', 'this', 'link'):
            self.log_error(file, line, f"Link text is not informative: {text}", logging.INFO)
        elif not text:
            error = f"Image has no alt text: {original_text}" if is_image else f"Link text is empty: {original_text}"
            self.log_error(file, line, error, logging.ERROR)

        # Validate the title
        if title is not None:
            if not (title.startswith('"') and title.endswith('"')):
                self.log_error(file, line, f"Title is not quoted: {original_text}", logging.ERROR)
            elif title == title.strip('"'):
                self.log_error(file, line, f"Title is empty: {original_text}", logging.ERROR)

        # Validate the URL
        if not url:
            self.log_error(file, line, f"Missing URL: {original_text}", logging.ERROR)
        elif not url.startswith(('/', '#', 'http://', 'https://', 'mailto:', 'tel:')):
            self.log_error(file, line, f"Relative or invalid URL: {original_text}", logging.WARNING)
        else:
            if url.startswith(('http://', 'https://')):
                try:
                    cleaned_url = self.unescape_url(url)
                    if cleaned_url not in self.response_cache:
                        self.response_cache[cleaned_url] = requests.get(cleaned_url, timeout=5, headers={
                            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
                        })
                    response = self.response_cache[cleaned_url]
                    status_code = response.status_code
                except ConnectionError:
                    self.log_error(file, line, f"Connection error: {cleaned_url}", logging.ERROR)
                except requests.exceptions.RequestException as exc:
                    self.log_error(file, line, f"URL {type(exc).__name__}: {cleaned_url}", logging.ERROR)
                else:
                    if status_code in (404, 410):
                        self.log_error(file, line, f"URL returns HTTP {status_code}: {cleaned_url}", logging.ERROR)
                        archived_versions = requests.get(
                            'https://archive.org/wayback/available', params={'url': cleaned_url}
                        ).json()
                        latest_archive = archived_versions.get('archived_snapshots', {}).get('closest')
                        if latest_archive and latest_archive['status_code'] == '200':
                            new_text = match['first_half'] + match['second_half'].replace(
                                url, self.escape_url(latest_archive['url']))
                    elif status_code >= 400:
                        severity = logging.WARNING if status_code in (403, 503) else logging.ERROR
                        self.log_error(file, line, f"URL returns HTTP {status_code}: {cleaned_url}", severity)
                    elif response.history and response.history[-1].status_code == 301:
                        self.log_error(file, line, f"URL redirects: {cleaned_url} -> {response.url}", logging.INFO)
                        new_text = match['first_half'] + match['second_half'].replace(url, self.escape_url(response.url))
            elif url.startswith('/'):
                if is_image and not (config.content_path / url.lstrip('/')).exists():
                    self.log_error(file, line, f"Image not found: {url}", logging.ERROR)
                else:
                    pass
            elif url.startswith('#'):
                pass
            elif url.startswith(('mailto:', 'tel:')):
                pass
            else:
                self.log_error(file, line, f"Relative or invalid URL: {url}", logging.WARNING)

        if new_text != original_text:
            self.log_substitution(file, line, original_text, new_text)
        return new_text
