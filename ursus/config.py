from pathlib import Path
import logging


default_config = {
    'content_path': Path('content').resolve(),
    'templates_path': Path('templates').resolve(),
    'output_path': Path('output').resolve(),

    # The generator that makes something out of your content
    'generator': 'ursus.generators.static.StaticSiteGenerator',

    # The processors that update the context of individual entries
    'entry_context_processors': [
        'ursus.context_processors.markdown.MarkdownProcessor',
    ],

    # The processors that update the full context
    'global_context_processors': [
        'ursus.context_processors.get_entries.GetEntriesProcessor',
        'ursus.context_processors.related.RelatedEntriesProcessor',
    ],

    # The renderers that take your templates and content, and populate the output dir
    'renderers': [
        'ursus.renderers.jinja.JinjaRenderer',
        'ursus.renderers.static.StaticAssetRenderer',
        'ursus.renderers.image.ImageTransformRenderer',
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
