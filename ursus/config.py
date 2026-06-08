from markdown.extensions.wikilinks import build_url
from markdown.extensions.toc import slugify
from pathlib import Path
from platformdirs import user_cache_dir
from typing import Any, Callable
import logging


def default_context_processors() -> list[str]:
    return [
        "ursus.context_processors.stale.StaleEntriesProcessor",
        "ursus.context_processors.image.ImageProcessor",
        "ursus.context_processors.markdown.MarkdownProcessor",
        "ursus.context_processors.get_entries.GetEntriesProcessor",
        "ursus.context_processors.related.RelatedEntriesProcessor",
        # 'ursus.context_processors.git_date.GitDateProcessor',
    ]


def default_image_transforms(max_size: int = 5000) -> dict:
    return {
        "": {
            "max_size": (max_size, max_size),
        },
    }


def default_jinja_filters() -> dict[str, Any]:
    return {}


def default_jinja_extensions() -> list[Any]:
    return [
        "jinja2.ext.do",
        "ursus.renderers.jinja.JsLoaderExtension",
        "ursus.renderers.jinja.CssLoaderExtension",
        "ursus.renderers.jinja.ScssLoaderExtension",
        "ursus.renderers.jinja.ResponsiveImageExtension",
    ]


def default_linters() -> list[str]:
    return [
        "ursus.linters.markdown.MarkdownLinkTextsLinter",
        "ursus.linters.markdown.MarkdownLinkTitlesLinter",
        "ursus.linters.markdown.MarkdownInternalLinksLinter",
        "ursus.linters.markdown.MarkdownExternalLinksLinter",
        "ursus.linters.markdown.RelatedEntriesLinter",
        "ursus.linters.images.UnusedImagesLinter",
    ]


def default_markdown_extensions() -> dict:
    return {
        "codehilite": {
            "guess_lang": False,
        },
        "fenced_code": {},
        "jinja": {},
        "responsive_images": {},
        "smarty": {},
        "superscript": {},
        "tables": {},
        "base_url": {},
        "tasklist": {
            # The CSS class of Markdown list items with a checkbox ("- [ ] a list item")
            # Sets the class of the <li> and the <input type="checkbox">
            "list_item_class": None,
            "checkbox_class": None,
        },
        "toc": {
            "slugify": slugify,
        },
        "wikilinks": {
            # The base URL prepended to all markdown [[wikilinks]], without a trailing slash.
            # For example, https://allaboutberlin.com/glossary
            "base_url": "/",
            "end_url": "",
            "build_url": build_url,
            "html_class": None,
        },
        "better_footnotes": {
            "BACKLINK_TEXT": "⤴",
            "SUPERSCRIPT_TEXT": "{}",
        },
    }


def default_renderers() -> list[str]:
    return [
        "ursus.renderers.static.StaticAssetRenderer",
        "ursus.renderers.static.ArchiveRenderer",
        "ursus.renderers.image.ImageTransformRenderer",
        "ursus.renderers.jinja.JinjaRenderer",
        "ursus.renderers.lunr.LunrIndexRenderer",
        "ursus.renderers.sass.SassRenderer",
    ]


class UrsusConfig:
    # Allows ursus_config.py to add arbitrary attributes (e.g. API keys) without type checker errors.
    # Pyright suppresses reportAttributeAccessIssue for classes that define __setattr__ / __getattr__.
    def __setattr__(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(name)

    def __init__(self) -> None:
        self.content_path: Path = Path("content").resolve()
        self.templates_path: Path = Path("templates").resolve()
        self.output_path: Path = Path("output").resolve()
        self.cache_path: Path = Path(user_cache_dir("ursus", "nicolasb"))

        # The URL of this website's root, without a trailing slash. For example, https://allaboutberlin.com
        self.site_url: str = ""

        # The URL extension of HTML pages. Change this if your server changes or removes the file extension.
        self.html_url_extension: str = ".html"

        # Minify Javascript and CSS
        self.minify_js: bool = False
        self.minify_css: bool = False

        # Builds the static website faster by only rebuilding templates for files that changed.
        # Related pages might not be rebuilt, even if they might be affected by the changes.
        # If False, everything is rebuilt from scratch. It's recommended to disable fast_rebuilds in production.
        self.fast_rebuilds: bool = False

        # Sets the <img sizes=""> attribute for your content images
        self.image_default_sizes: str | None = None

        # Transforms applied to your content images
        self.image_transforms: dict = default_image_transforms()

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
        self.lunr_indexes: dict = {}
        self.lunr_index_output_path: Path = Path("search-index.json")  # Relative to output_path

        # The processors that update the context with extra data
        self.context_processors: list[str] = default_context_processors()
        self.context_globals: dict = {}

        self.markdown_extensions: dict = default_markdown_extensions()

        # The renderers that take your templates and content, and populate the output dir
        self.renderers: list[str] = default_renderers()

        # Linters look for errors in your content
        self.linters: list[str] = default_linters()

        # Filter functions available in Jinja templates. The key is the filter name, and the value is a function
        self.jinja_filters: dict[str, Callable] = default_jinja_filters()

        self.jinja_extensions: list[str] = default_jinja_extensions()

    logging = {
        "datefmt": "%Y-%m-%d %H:%M:%S",
        "format": "%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s",
        "level": logging.INFO,
    }

    def add_markdown_extension(self, name: str, config: dict[str, Any] = {}) -> None:
        self.markdown_extensions[name] = config


config = UrsusConfig()
