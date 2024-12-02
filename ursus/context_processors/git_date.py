from datetime import datetime
from pathlib import Path
from ursus.config import config
from ursus.context_processors import Context, ContextProcessor, EntryURI
import git
import logging


def unescape_backslashes(s: str, encoding: str = 'utf-8') -> str:
    """
    Convert backslash-escaped strings to normal strings
    ("DerHimmel\303\234berBerlin" -> "DerHimmelÜberBerlin")
    """
    return (s.encode('latin1')
             .decode('unicode-escape')
             .encode('latin1')
             .decode(encoding))


class GitDateProcessor(ContextProcessor):
    """
    Sets entry.date_updated to the date of the latest commit.
    """

    def __init__(self: 'GitDateProcessor'):
        super().__init__()
        self.entry_uri_commit_dates: dict[EntryURI, datetime] = {}
        if not config.fast_rebuilds:
            self.repo = git.Repo(config.content_path, search_parent_directories=True)
            self.repo_root = Path(self.repo.working_dir)

            commit_date = None
            git_log = self.repo.git.log('--format=">>>%cd"', '--date=unix', '--name-only', '--encoding=UTF-8')
            for line in git_log.split('\n'):
                # Remove wrapping quotes, convert backslash-escaped unicode characters back to unicode
                line = unescape_backslashes(line.strip('"'))
                if line.startswith('>>>'):
                    commit_date = datetime.fromtimestamp(int(line.removeprefix('>>>'))).astimezone()
                elif len(line) > 0:
                    entry_uri = self.commit_path_to_entry_uri(line)
                    if entry_uri in self.entry_uri_commit_dates:
                        self.entry_uri_commit_dates[entry_uri] = max(commit_date, self.entry_uri_commit_dates[entry_uri])
                    else:
                        self.entry_uri_commit_dates[entry_uri] = commit_date

    def commit_path_to_entry_uri(self, commit_path: str) -> EntryURI | None:
        abs_commit_path = self.repo_root / commit_path
        try:
            return EntryURI(str(abs_commit_path.relative_to(config.content_path)))
        except ValueError:
            return None

    def process(self, context: Context, changed_files: set[Path] | None = None) -> Context:
        for entry_uri, entry in context['entries'].items():
            if entry_uri in self.entry_uri_commit_dates:
                entry['date_updated'] = self.entry_uri_commit_dates.get(entry_uri)
            else:
                if not config.fast_rebuilds:
                    logging.warning(f"Entry {entry_uri} has no commit date")
                entry['date_updated'] = datetime.now().astimezone()
        return context
