from . import Renderer
from lunr import lunr
from pathlib import Path
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
    def __init__(self, config):
        super().__init__(config)
        self.index_config = config['lunr_indexes']
        self.index_output_path = self.output_path / config['lunr_index_output_path']

    def render(self, context: dict, changed_files: set = None, fast: bool = False) -> set:
        logger.info(f"Generating search index at {self.index_output_path}")

        indexed_documents = []
        returned_documents = {}

        for index in self.index_config['indexes']:
            for entry_uri, entry in context['entries'].items():
                if Path(entry_uri).match(index['uri_pattern']):
                    indexed_documents.append((
                        {
                            'uri': entry_uri,
                            **{field: entry.get(field, '') for field in self.index_config['indexed_fields']},
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
            fields=self.index_config['indexed_fields'],
            documents=indexed_documents
        )

        self.index_output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.index_output_path.open('w+') as index_file:
            json.dump({
                'index': index.serialize(),
                'documents': returned_documents,
            }, index_file)
