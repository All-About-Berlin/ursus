from ursus.utils import get_files_in_path
from ursus.config import config


class ContextProcessor:
    def process(self, context: dict, changed_files: set = None) -> dict:
        return context


class EntryContextProcessor(ContextProcessor):
    def process(self, context: dict, changed_files: set = None) -> dict:
        for file_path in get_files_in_path(config.content_path, changed_files):
            entry_uri = str(file_path)
            entry = context['entries'].get(entry_uri, {})
            context['entries'][entry_uri] = self.process_entry(entry_uri, entry)

            assert context['entries'][entry_uri] is not None, \
                "{type(self).__name__}.process_entry is returning None instead of the entry context."

        return context

    def process_entry(self, entry_uri: str, entry_context: dict) -> dict:
        raise NotImplementedError
