from collections import UserDict
from . import ContextProcessor


class IndexProcessor(ContextProcessor):
    """
    Adds index entries that return a dict of all entries in that namespace.

    For example, 'guides' is a {uri: context} dict of all entries starting with 'guides/'.
    """
    class IndexDict(UserDict):
        def __getitem__(self, key):
            if key not in self.data:
                entry_uris = [
                    entry_uri for entry_uri in self.data.keys()
                    if entry_uri.startswith(key + '/')
                ]
                # If there are no entries, fall back to default behaviour
                if entry_uris:
                    return {
                        entry_uri: self.data[entry_uri]
                        for entry_uri in entry_uris
                    }
            return super().__getitem__(key)

    def process(self, full_context: dict, changed_files=None):
        if not isinstance(full_context['entries'], self.IndexDict):
            full_context['entries'] = self.IndexDict(full_context['entries'])
        return full_context
