from pathlib import Path
import logging


config = {
    'content_path': Path('content').resolve(),
    'templates_path': Path('templates').resolve(),
    'output_path': Path('output').resolve(),

    # The generator that makes something out of your content
    'generator': 'ursus.generators.static.StaticSiteGenerator',

    # Rebuilds the output faster by only rebuilding templates for the changed files.
    # Related pages (like index pages) will not be rebuild, even though they could change.
    # If false, the pages that definitely changed are still rebuilt before others.
    'fast_rebuilds': False,

    # The processors that update the context with extra data
    'context_processors': [
        'ursus.context_processors.stale.StaleEntriesProcessor',
        'ursus.context_processors.markdown.MarkdownProcessor',
        'ursus.context_processors.get_entries.GetEntriesProcessor',
        'ursus.context_processors.related.RelatedEntriesProcessor',
    ],

    # The renderers that take your templates and content, and populate the output dir
    'renderers': [
        'ursus.renderers.static.StaticAssetRenderer',
        'ursus.renderers.image.ImageTransformRenderer',
        'ursus.renderers.jinja.JinjaRenderer',
    ],

    # Transforms applied to your content images
    'image_transforms': {
        '': {
            'max_size': (5000, 5000),
        },
    },

    # The URL of this website's root, without a trailing slash. For example, https://allaboutberlin.com
    'site_url': '',

    # The base URL prepended to all markdown [[wikilinks]], without a trailing slash.
    # For example, https://allaboutberlin.com/glossary
    'wikilinks_base_url': '',

    # The URL extension of HTML pages. Change this if your server changes or removes the file extension.
    'html_url_extension': '.html',

    # Variables at the root of the template context
    'globals': {},

    # Filter functions available in Jinja templates
    'jinja_filters': {},

    # Logger configuration
    'logging': {
        'datefmt': '%Y-%m-%d %H:%M:%S',
        'fmt': '%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s',
        'level': logging.INFO,
    }
}
