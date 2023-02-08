from datetime import datetime
from ursus.context_processors import EntryContextProcessor
import git


class GitDateProcessor(EntryContextProcessor):
    """
    Sets entry.date_updated to the date of the latest commit.
    """
    def __init__(self, config: dict):
        super().__init__(config)
        git_repo = git.Repo(self.content_path, search_parent_directories=True)
        self.git = git.Git(git_repo.working_dir)

    def process_entry(self, entry_uri: str, entry_context: dict) -> dict:
        entry_path = self.content_path / entry_uri
        last_commit_timestamp = self.git.log(
            '-n', 1,
            f'--pretty=%at',
            '--',
            entry_path
        )
        assert last_commit_timestamp
        entry_context['date_updated'] = datetime.fromtimestamp(int(last_commit_timestamp))
        return entry_context
