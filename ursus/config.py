from datetime import datetime
from pathlib import Path
import logging


config = {
    'globals': {
        'site_url': 'https://allaboutberlin.com/',
        'now': datetime.now(),
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
                ],
                'content_path': Path('site/content').resolve(),
                'templates_path': Path('site/templates').resolve(),
                'output_path': Path('dist').resolve(),
                'wikilinks_base_url': 'https://allaboutberlin.com/glossary/',
            }
        ),
    ],
    'logging': {
        'datefmt': '%Y-%m-%d %H:%M:%S',
        'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        'level': logging.INFO,
    }
}
