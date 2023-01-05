from datetime import datetime
from pathlib import Path
import logging


config = {
    # These variables are included in the context of every template
    'globals': {
        'site_url': 'https://allaboutberlin.com',
        'now': datetime.now(),
    },

    # Where the pages and assets are stored
    'content_path': Path('site/content').resolve(),

    # The generators to use
    'generators': [
        (
            'generators.StaticSiteGenerator',
            {
                'base_url': 'https://allaboutberlin.com',
                'file_processors': ['file_processors.MarkdownProcessor'],
                'templates_path': Path('site/templates').resolve(),
                'output_path': Path('dist').resolve(),
            }
        ),
    ],
    'logging': {
        'datefmt': '%Y-%m-%d %H:%M:%S',
        'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        'level': logging.INFO,
    }
}
