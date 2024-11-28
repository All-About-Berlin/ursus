from . import ContextProcessor, Entry, EntryURI
from operator import itemgetter
from functools import partial
from typing import Callable


def first_existing_item_getter(keys: list[str]):
    """
    Returns the value of the first existing key from a list of dictionary keys

    Args:
        keys (list[str]): A list of dictionary keys
    """
    def get_value(entry: dict):
        return list(
            filter(None, [entry.get(key) for key in keys])
        )[0]
    return get_value


def get_entries(
    entries: dict[EntryURI, Entry],
    namespaces: str | list[str] | None = None,
    filter_by: Callable | None = None,
    sort_by: Callable | str | list[str] | None = None,
    reverse: bool = False
) -> list[Entry]:
    """Returns a sorted, filtered list of entries

    Args:
        entries (dict): The dictionary of entries.
        namespace (str, list[str], optional): Only returns entries in the given namespace(s) (for example "posts" or "blog/posts"). In other
            words, only return entries in a given directory (like <content_path>/posts or <content_path>/blog/posts).
        filter_by (Callable, optional): Filter the items by the given filtering function.
        sort_by (Callable | str | list[str], optional): Sort items by the given dict key, list of dict keys, or value
            returned by the given function
        reverse (bool, optional): Reverse the sorting order
    """
    if namespaces:
        namespace_list = [namespaces, ] if isinstance(namespaces, str) else namespaces
        entries = {
            uri: value for uri, value in entries.items()
            if uri.startswith(tuple(ns + '/' for ns in namespace_list))
        }

    if filter_by:
        entries = {
            uri: value for uri, value in entries.items()
            if filter_by(uri, value)
        }

    entry_list = list(entries.values())

    if sort_by:
        if callable(sort_by):
            sorter = sort_by
        elif isinstance(sort_by, str):
            sorter = itemgetter(sort_by)
        else:
            sorter = first_existing_item_getter(sort_by)
        entry_list = sorted(entry_list, key=sorter, reverse=reverse)

    return entry_list


class GetEntriesProcessor(ContextProcessor):
    """
    Adds the get_entries() method to the context root. This function filters and
    sorts entries.
    """

    def process(self, context, changed_files=None):
        if 'get_entries' not in context:
            context['get_entries'] = partial(get_entries, context['entries'])
        return context
