from . import ContextProcessor
from operator import itemgetter


class GetEntriesProcessor(ContextProcessor):
    """
    Adds the get_entries() method to the context root
    """
    def process(self, context: dict, changed_files: set = None) -> dict:
        def get_entries(namespace, filter_by=None, sort_by=None, reverse=False):
            entries = context['entries']
            if namespace:
                entries = {
                    uri: value for uri, value in entries.items()
                    if uri.startswith(namespace + '/')
                }

            if filter_by:
                entries = {
                    uri: value for uri, value in entries.items()
                    if filter_by(uri, value)
                }

            entries = entries.values()

            if sort_by:
                if callable(sort_by):
                    sorter = sort_by
                elif isinstance(sort_by, str):
                    sorter = itemgetter(sort_by)
                else:
                    sorter = lambda x: list(filter(None, [x.get(key) for key in sort_by]))[0]
                entries = sorted(entries, key=sorter, reverse=reverse)

            return entries

        if get_entries not in context:
            context['get_entries'] = get_entries

        return context
