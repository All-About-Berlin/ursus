from collections import UserDict
from . import ContextProcessor


class IndexProcessor(ContextProcessor):
    """
    Adds index entries that contain a list of all entries in that namespace.

    For example, 'guides' is a list of all entries starting with 'guides/'.
    """
    class IndexDict(UserDict):
        def __getitem__(self, key):
            if key not in self.data:
                return [
                    self.data[child_key]
                    for child_key in self.data.keys() if child_key.startswith(key + '/')
                ]
            return super().__getitem__(key)

    def __init__(self, **config):
        pass

    def process(self, full_context: dict):
        full_context['entries'] = self.IndexDict(full_context['entries'])
        return full_context

