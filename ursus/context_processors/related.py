from collections import UserDict
from . import ContextProcessor


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
                if isinstance(related_value, str):  # Single URI string
                    return [self.all_entries[related_value]]
                else:  # List of URI strings
                    return [self.all_entries[subvalue] for subvalue in related_value]
            return super().__getitem__(key)

    def __init__(self, **config):
        pass

    def process(self, full_context: dict, changed_files=None):
        for uri, entry in full_context['entries'].items():
            if type(full_context['entries'][uri]) is not self.RelatedEntryReferenceDict:
                full_context['entries'][uri] = self.RelatedEntryReferenceDict(entry, full_context['entries'])

        return full_context
