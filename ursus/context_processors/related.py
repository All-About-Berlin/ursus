from collections import UserDict
from . import ContextProcessor, Entry, EntryURI
import sys


class RelatedEntryReferenceDict(UserDict):
    def __init__(self, entry: Entry, all_entries: dict[EntryURI, Entry]):
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


class RelatedEntriesProcessor(ContextProcessor):
    """
    Entry fields that start with related_* return a list of entries, instead of
    a list of entry URIs.
    """

    def process(self, context, changed_files=None):
        for uri, entry in context['entries'].items():
            if not isinstance(context['entries'][uri], RelatedEntryReferenceDict):
                context['entries'][uri] = RelatedEntryReferenceDict(entry, context['entries'])

        return context
