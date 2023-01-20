from pathlib import Path
import logging


config = {
    # These variables are directly available in every renderer's context
    'globals': {
    },
    'generators': [
        (
            'ursus.generators.static.StaticSiteGenerator', {
                'file_context_processors': [
                    'ursus.context_processors.markdown.MarkdownProcessor',
                ],
                'context_processors': [
                    'ursus.context_processors.index.IndexProcessor',
                    'ursus.context_processors.related.RelatedEntriesProcessor',
                ],
                'renderers': [
                    'ursus.renderers.jinja.JinjaRenderer',
                    'ursus.renderers.static.StaticAssetRenderer',
                    'ursus.renderers.image.ImageTransformRenderer',
                ],
                'content_path': Path('content').resolve(),
                'templates_path': Path('templates').resolve(),
                'output_path': Path('output').resolve(),

                """
                # Uncomment to resize your content images to different sizes
                'image_transforms': {
                    '': {  # Default image size
                        'exclude': '*.pdf',
                        'max_size': (3200, 4800),
                    },
                    'thumbnails': {
                        'exclude': ('*.pdf', '*.svg'),
                        'max_size': (400, 400),
                        'output_types': ('original', 'webp'),
                    },
                    'pdfPreviews': {
                        'include': ('documents/*.pdf', 'forms/*.pdf'),
                        'max_size': (300, 500),
                        'output_types': ('webp', 'png'),
                    }
                },
                """

                # The root URL of this website, without a trailing slash. For example, https://allaboutberlin.com
                'site_url': '',

                # The base URL prepended to all markdown wikilinks, without a trailing slash.
                # For example, https://allaboutberlin.com/glossary
                'wikilinks_base_url': '',

                # The URL extension of HTML pages. Change this if your server changes or removes the file extension.
                'html_url_extension': '.html',
            }
        ),
    ],
    'logging': {
        'datefmt': '%Y-%m-%d %H:%M:%S',
        'fmt': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        'level': logging.INFO,
    }
}
