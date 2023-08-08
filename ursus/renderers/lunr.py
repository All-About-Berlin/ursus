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

    def get_index_for_entry(self, index_config: dict, entry_uri: str, entry: dict):
        if Path(entry_uri).match(index_config['uri_pattern']):
            # Data used to build the Lunr.js index (indexed fields, document boost)
            indexed_document = (
                {
                    **{field: entry.get(field, '') for field in config.lunr_indexes['indexed_fields']},
                },
                {
                    'boost': index_config.get('boost', 1)
                }
            )

            # Metadata about the documents, used to render the search box (title, URL, etc)
            returned_document = {
                field: entry.get(field) for field in index_config['returned_fields']
            }

            yield indexed_document, returned_document

    def render(self, context: dict, changed_files: set = None) -> set:
        if config.fast_rebuilds:
            return set()

        index_output_path = config.output_path / config.lunr_index_output_path
        logger.info(f"Generating search index at {config.lunr_index_output_path}")

        indexed_documents = []
        returned_documents = {}

        document_ref = 0
        for index_config in config.lunr_indexes.get('indexes', []):
            for entry_uri, entry in context['entries'].items():
                for indexed_document, returned_document in self.get_index_for_entry(index_config, entry_uri, entry):
                    # indexed_document contains the fields that are included in the Lunr index
                    # returned_document contains information about the entry (title, URL)
                    # The ref attribute connects a Lunr search result to a returned_document
                    indexed_document[0]['ref'] = document_ref
                    indexed_documents.append(indexed_document)
                    returned_documents[document_ref] = returned_document
                    document_ref += 1

        index = lunr(
            ref='ref',
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
