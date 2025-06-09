from dataclasses import dataclass, field
from markdown.extensions.wikilinks import build_url
from markdown.extensions.toc import slugify
from pathlib import Path
from platformdirs import user_cache_dir
from typing import Any, Callable, Iterable
import logging


def default_context_processors() -> list[str]:
    return [
        'ursus.context_processors.stale.StaleEntriesProcessor',
        'ursus.context_processors.image.ImageProcessor',
        'ursus.context_processors.markdown.MarkdownProcessor',
        'ursus.context_processors.get_entries.GetEntriesProcessor',
        'ursus.context_processors.related.RelatedEntriesProcessor',
        # 'ursus.context_processors.git_date.GitDateProcessor',
    ]


def default_image_transforms(max_size: int = 5000) -> dict:
    return {
        '': {
            'max_size': (max_size, max_size),
        },
    }


def default_jinja_filters() -> dict[str, Any]:
    return {}


def default_linters() -> list[str]:
    return [
        'ursus.linters.markdown.MarkdownLinkTextsLinter',
        'ursus.linters.markdown.MarkdownLinkTitlesLinter',
        'ursus.linters.markdown.MarkdownInternalLinksLinter',
        'ursus.linters.markdown.MarkdownExternalLinksLinter',
        'ursus.linters.markdown.RelatedEntriesLinter',
        'ursus.linters.images.UnusedImagesLinter',
    ]


def default_markdown_extensions() -> dict:
    return {
        'codehilite': {
            'guess_lang': False,
        },
        'fenced_code': {},
        'jinja': {},
        'meta': {},
        'responsive_images': {},
        'smarty': {},
        'superscript': {},
        'tables': {},
        'tasklist': {
            # The CSS class of Markdown list items with a checkbox ("- [ ] a list item")
            # Sets the class of the <li> and the <input type="checkbox">
            'list_item_class': None,
            'checkbox_class': None,
        },
        'toc': {
            'slugify': slugify,
        },
        'wikilinks': {
            # The base URL prepended to all markdown [[wikilinks]], without a trailing slash.
            # For example, https://allaboutberlin.com/glossary
            'base_url': '/',
            'end_url': '',
            'build_url': build_url,
            'html_class': None,
        },
        'better_footnotes': {
            'BACKLINK_TEXT': '⤴',
            'SUPERSCRIPT_TEXT': '{}',
        },
    }


def default_renderers() -> list[str]:
    return [
        'ursus.renderers.static.StaticAssetRenderer',
        'ursus.renderers.static.ArchiveRenderer',
        'ursus.renderers.image.ImageTransformRenderer',
        'ursus.renderers.jinja.JinjaRenderer',
        'ursus.renderers.lunr.LunrIndexRenderer',
        'ursus.renderers.sass.SassRenderer',
    ]


@dataclass
class UrsusConfig():
    content_path: Path = Path('content').resolve()
    templates_path: Path = Path('templates').resolve()
    output_path: Path = Path('output').resolve()
    cache_path: Path = Path(user_cache_dir('ursus', 'nicolasb'))

    # The URL of this website's root, without a trailing slash. For example, https://allaboutberlin.com
    site_url: str = ''

    # The URL extension of HTML pages. Change this if your server changes or removes the file extension.
    html_url_extension: str = '.html'

    # Minify Javascript and CSS
    minify_js: bool = False
    minify_css: bool = False

    # Builds the static website faster by only rebuilding templates for files that changed.
    # Related pages might not be rebuilt, even if they might be affected by the changes.
    # If False, everything is rebuilt from scratch. It's recommended to disable fast_rebuilds in production.
    fast_rebuilds: bool = False

    # Sets the <img sizes=""> attribute for your content images
    image_default_sizes: str | None = None

    # Transforms applied to your content images
    image_transforms: dict = field(default_factory=default_image_transforms)

    """
    Parametres to generate a search index for lunr.js
    Example:
    {
        'indexed_fields': ('body', ),  # Index these fields only
        'indexes': [
            {
                'uri_pattern': '*.md',  # Index entries with URIs that match this glob pattern
                'returned_fields': ('body', 'url', ),  # Return these fields only in the document list
                'boost': 1,  # Documents matching this pattern should be boosted n times over others
            },
        ]
    }
    """
    lunr_indexes: dict = field(default_factory=dict)
    lunr_index_output_path: Path = Path('search-index.json')  # Relative to output_path

    generator: str = 'ursus.generators.static.StaticSiteGenerator'

    # The processors that update the context with extra data
    context_processors: list[str] = field(default_factory=default_context_processors)
    context_globals: dict = field(default_factory=dict)

    markdown_extensions: dict = field(default_factory=default_markdown_extensions)

    # Translations
    translations_path: Path = Path('templates/_translations').resolve()
    default_language: str | None = None
    translation_languages: Iterable[str] | None = None

    openai_api_key: str | None = None
    metadata_fields_to_translate: Iterable[str] = ()

    # The renderers that take your templates and content, and populate the output dir
    renderers: list[str] = field(default_factory=default_renderers)

    # Linters look for errors in your content
    linters: list[str] = field(default_factory=default_linters)

    # Filter functions available in Jinja templates. The key is the filter name, and the value is a function
    jinja_filters: dict[str, Callable] = field(default_factory=default_jinja_filters)

    logging = {
        'datefmt': '%Y-%m-%d %H:%M:%S',
        'format': '%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s',
        'level': logging.INFO,
    }

    def add_markdown_extension(self, name: str, config: dict[str, Any] = {}) -> None:
        self.markdown_extensions[name] = config


config = UrsusConfig()
