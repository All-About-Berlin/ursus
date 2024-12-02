from . import Context, ContextProcessor, Entry, EntryURI
from collections import UserDict
from pathlib import Path
from typing import Any
import sys


class RelatedEntryReferenceDict(UserDict[str, Any]):
    def __init__(self, entry: Entry, all_entries: dict[EntryURI, Entry]):
        self.all_entries = all_entries
        super().__init__(entry)

    def __getitem__(self, key: str) -> Any:
        if key.startswith('related_') and key in self.data:
            related_value: list[str] | str = self.data[key]
            try:
                if isinstance(related_value, str):  # Single URI string
                    return [self.all_entries[EntryURI(related_value)]]
                else:  # List of URI strings
                    return [self.all_entries[EntryURI(subvalue)] for subvalue in related_value]
            except KeyError:
                raise ValueError(f"{key} contains invalid value {sys.exc_info()[1]}")
        return super().__getitem__(key)


class RelatedEntriesProcessor(ContextProcessor):
    """
    Entry fields that start with related_* return a list of entries, instead of
    a list of entry URIs.
    """

    def process(self, context: Context, changed_files: set[Path] | None = None) -> Context:
        for uri, entry in context['entries'].items():
            if not isinstance(context['entries'][uri], RelatedEntryReferenceDict):
                context['entries'][uri] = RelatedEntryReferenceDict(entry, context['entries'])

        return context
