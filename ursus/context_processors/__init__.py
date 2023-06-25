from ursus.utils import get_files_in_path
from ursus.config import config


class ContextProcessor:
    def process(self, context: dict, changed_files: set = None) -> dict:
        """Transforms the context and returns it. The context is used to render templates.

        Args:
            context (dict): An object that represents all data used to render templates
                (website info, blog posts, utility functions, etc.)
            changed_files (set, optional): A list of files that changed since the last context update.

        Returns:
            dict: The updated context
        """
        return context


class EntryContextProcessor(ContextProcessor):
    def process(self, context: dict, changed_files: set = None) -> dict:
        for file_path in get_files_in_path(config.content_path, changed_files):
            entry_uri = str(file_path)
            context['entries'].setdefault(entry_uri, {})
            self.process_entry(context, entry_uri)
        return context

    def process_entry(self, context: dict, entry_uri: str):
        raise NotImplementedError
