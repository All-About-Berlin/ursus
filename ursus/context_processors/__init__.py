from collections import UserDict
from pathlib import Path
from typing import Any, NewType


EntryURI = NewType('EntryURI', str)
Entry = NewType('Entry', dict[str, Any])


class Context(UserDict[str, Any]):
    pass


class ContextProcessor:
    def process(self, context: Context, changed_files: set[Path] | None = None) -> Context:
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
    def process(self, context: Context, changed_files: set[Path] | None = None) -> Context:
        for entry_uri in list(context['entries'].keys()):
            self.process_entry(context, entry_uri, changed_files)
        return context

    def process_entry(self, context: Context, entry_uri: EntryURI, changed_files: set[Path] | None = None) -> None:
        raise NotImplementedError
