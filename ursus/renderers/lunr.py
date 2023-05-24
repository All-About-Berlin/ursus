from . import Renderer
from lunr import lunr
from pathlib import Path
from ursus.config import config
import json
import logging


logger = logging.getLogger(__name__)


class LunrIndexRenderer(Renderer):
    """
    Renders a .json search index for Lunr.js. The resulting file is a dictionary
    with two keys:

    - 'index': An index object that can be passed to Lunr.js
    - 'documents': A dict of entry URI to documents that can be used to render
        search results (titles, URLs, excerpts, etc.)
    """
    def __init__(self):
        super().__init__()

    def render(self, context: dict, changed_files: set = None) -> set:
        if config.fast_rebuilds:
            return set()

        index_output_path = config.output_path / config.lunr_index_output_path
        logger.info(f"Generating search index at {config.lunr_index_output_path}")

        indexed_documents = []
        returned_documents = {}

        for index in config.lunr_indexes.get('indexes', []):
            for entry_uri, entry in context['entries'].items():
                if Path(entry_uri).match(index['uri_pattern']):
                    indexed_documents.append((
                        {
                            'uri': entry_uri,
                            **{field: entry.get(field, '') for field in config.lunr_indexes['indexed_fields']},
                        },
                        {
                            'boost': index.get('boost', 1)
                        }
                    ))

                    returned_documents[entry_uri] = {
                        field: entry.get(field) for field in index['returned_fields']
                    }

        index = lunr(
            ref='uri',
            fields=config.lunr_indexes.get('indexed_fields', []),
            documents=indexed_documents
        )

        index_output_path.parent.mkdir(parents=True, exist_ok=True)
        with index_output_path.open('w+') as index_file:
            json.dump({
                'index': index.serialize(),
                'documents': returned_documents,
            }, index_file)

        return set([config.lunr_index_output_path])
