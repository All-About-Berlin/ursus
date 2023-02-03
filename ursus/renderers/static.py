from . import Renderer
from ursus.utils import get_files_in_path, copy_file
import logging


logger = logging.getLogger(__name__)


class StaticAssetRenderer(Renderer):
    """
    Copies static assets in `templates_path` to `output_path`.
    """
    ignored_suffixes = ('.jinja', )

    def get_assets_to_copy(self, changed_files=None):
        return [
            f for f in get_files_in_path(self.templates_path)
            if f.suffix not in self.ignored_suffixes
        ]

    def render(self, context: dict, changed_files=None, fast=False):
        for asset_path in self.get_assets_to_copy():
            abs_output_path = self.output_path / asset_path

            if changed_files is None or self.templates_path / asset_path in changed_files:
                logger.info('Copying asset %s', str(asset_path))
                copy_file(self.templates_path / asset_path, abs_output_path)
            else:
                abs_output_path.touch()  # Update mtime to avoid deletion
