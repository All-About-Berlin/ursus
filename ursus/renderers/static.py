from . import Renderer
from ursus.config import config
from ursus.utils import get_files_in_path, copy_file
import logging


logger = logging.getLogger(__name__)


class StaticAssetRenderer(Renderer):
    """
    Copies static assets in `templates_path` to `output_path`.
    """
    ignored_suffixes = ('.jinja', )

    def get_assets_to_copy(self, changed_files: set = None):
        return [
            f for f in get_files_in_path(config.templates_path)
            if f.suffix.lower() not in self.ignored_suffixes
        ]

    def render(self, context: dict, changed_files: set = None) -> set:
        files_to_keep = set()
        for asset_path in self.get_assets_to_copy():
            abs_output_path = config.output_path / asset_path

            if changed_files is None or config.templates_path / asset_path in changed_files:
                logger.info('Copying asset %s', str(asset_path))
                copy_file(config.templates_path / asset_path, abs_output_path)
            files_to_keep.add(asset_path)

        return files_to_keep
