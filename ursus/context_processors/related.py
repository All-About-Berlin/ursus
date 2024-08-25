from collections import UserDict
from . import ContextProcessor
import sys


class RelatedEntriesProcessor(ContextProcessor):
    """
    Entry fields that start with related_* return a list of entries, instead of
    a list of entry URIs.
    """
    class RelatedEntryReferenceDict(UserDict):
        def __init__(self, entry, all_entries):
            self.all_entries = all_entries
            super().__init__(entry)

        def __getitem__(self, key):
            if key.startswith('related_') and key in self.data:
                related_value = self.data[key]
                try:
                    if isinstance(related_value, str):  # Single URI string
                        return [self.all_entries[related_value]]
                    else:  # List of URI strings
                        return [self.all_entries[subvalue] for subvalue in related_value]
                except KeyError:
                    raise ValueError(f"{key} contains invalid value {sys.exc_info()[1]}")
            return super().__getitem__(key)

    def process(self, context: dict, changed_files: set = None) -> dict:
        for uri, entry in context['entries'].items():
            if not isinstance(context['entries'][uri], self.RelatedEntryReferenceDict):
                context['entries'][uri] = self.RelatedEntryReferenceDict(entry, context['entries'])

        return context
