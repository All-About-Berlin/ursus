from datetime import datetime
from pathlib import Path
from ursus.config import config
from ursus.context_processors import ContextProcessor
import git


class GitDateProcessor(ContextProcessor):
    """
    Sets entry.date_updated to the date of the latest commit.
    """
    def __init__(self):
        super().__init__()
        if not config.fast_rebuilds:
            self.repo = git.Repo(config.content_path, search_parent_directories=True)
            self.repo_root = Path(self.repo.working_dir)

    def commit_path_to_entry_uri(self, commit_path: str):
        abs_commit_path = self.repo_root / commit_path
        try:
            return str(abs_commit_path.relative_to(config.content_path))
        except ValueError:
            return None

    def process(self, context: dict, changed_files: set = None) -> dict:
        if not config.fast_rebuilds:
            for commit in self.repo.iter_commits("master"):
                commit_date = datetime.fromtimestamp(commit.authored_date)
                for file in self.repo.git.show(commit.hexsha, name_only=True, diff_filter='ACMR').split('\n'):
                    entry_uri = self.commit_path_to_entry_uri(file)
                    if entry_uri and entry_uri in context['entries']:
                        entry = context['entries'][entry_uri]
                        if not entry.get('date_updated') or commit_date > entry['date_updated']:
                            entry['date_updated'] = commit_date

        for entry in context['entries'].values():
            entry.setdefault('date_updated', datetime.now())
        return context
