from datetime import datetime
from pathlib import Path
import logging


config = {
    # These variables are included in the context of every template
    'globals': {
        'site_url': 'https://allaboutberlin.com/',
        'now': datetime.now(),
    },
    'generators': [
        (
            'generators.StaticSiteGenerator', {
                'file_context_processors': [
                    'file_context_processors.MarkdownContextProcessor',
                ],
                'context_processors': [
                    'context_processors.IndexProcessor',
                    'context_processors.RelatedEntriesProcessor',
                ],
                'renderers': [
                    'renderers.JinjaRenderer',
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
