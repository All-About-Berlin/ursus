from ursus.context_processors.get_entries import get_entries


entries = {
    'blog/hello.md': {
        'title': 'Hello world',
        'month': 'January',
        'short_title': 'Hello',
        'description': 'First post on this blog!',
    },
    'blog/bonjour.md': {
        'title': 'Bonjour monde',
        'month': 'October',
        'short_title': 'Bonjour',
        'description': 'Deuxième post sur ce blogue',
    },
    'blog/hallo.md': {
        'title': 'Hallo Welt',
        'month': 'September',
        'short_title': 'Hallo',
        'description': 'Dritter Beitrag auf diesem Blog',
    },
    'recipes/pancakes.md': {
        'title': 'Pancake recipe',
        'description': 'Flat and delicious',
        'ingredients': ['Flour', 'eggs', 'milk'],
    },
    'home.md': {
        'title': 'Home page',
        'content': 'Boy, what a home page!',
    },
    'empty.md': {
    },
}


def test_sort_by_function():
    def month_getter(entry):
        return [
            'January',
            'February',
            'March',
            'April',
            'May',
            'June',
            'July',
            'August',
            'September',
            'October',
            'November',
            'December',
        ].index(entry['month'])

    assert get_entries(entries, 'blog', sort_by=month_getter) == [
        entries['blog/hello.md'],
        entries['blog/hallo.md'],
        entries['blog/bonjour.md'],
    ]


def test_sort_by_one_key():
    assert get_entries(entries, 'blog', sort_by='title') == [
        entries['blog/bonjour.md'],
        entries['blog/hallo.md'],
        entries['blog/hello.md'],
    ]


def test_sort_by_multiple_keys():
    assert get_entries(entries, 'blog', sort_by=['short_title', 'title']) == [
        entries['blog/bonjour.md'],
        entries['blog/hallo.md'],
        entries['blog/hello.md'],
    ]


def test_filter_by():
    def uri_length_filter(entry_uri, entry):
        return len(entry_uri) <= 13

    filtered_entries = get_entries(entries, None, filter_by=uri_length_filter)
    assert len(filtered_entries) == 4
    assert entries['blog/hallo.md'] in filtered_entries
    assert entries['blog/hello.md'] in filtered_entries
    assert entries['home.md'] in filtered_entries
    assert entries['empty.md'] in filtered_entries


def test_no_namespace():
    assert len(get_entries(entries)) == 6


def test_namespace():
    assert get_entries(entries, 'recipes') == [
        entries['recipes/pancakes.md'],
    ]
