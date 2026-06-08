from pathlib import Path
from typing import Any, NewType


EntryURI = NewType("EntryURI", str)
Entry = NewType("Entry", dict[str, Any])

type Context = dict[str, Any]


class ContextProcessor:
    def process(self, context: Context, changed_files: set[Path] | None = None) -> None:
        """Transforms the context in-place. The context is used to render templates.

        Args:
            context (dict): An object that represents all data used to render templates
                (website info, blog posts, utility functions, etc.)
            changed_files (set, optional): A list of files that changed since the last context update.
        """
        pass


class EntryContextProcessor(ContextProcessor):
    def process(self, context: Context, changed_files: set[Path] | None = None) -> None:
        from ursus.config import config
        for entry_uri in list(context["entries"].keys()):
            if config.fast_rebuilds and changed_files is not None and (config.content_path / entry_uri) not in changed_files:
                continue
            self.process_entry(context, entry_uri)

    def process_entry(self, context: Context, entry_uri: EntryURI) -> None:
        raise NotImplementedError
