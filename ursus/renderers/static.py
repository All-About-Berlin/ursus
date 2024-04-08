from . import Renderer
from ursus.config import config
from ursus.utils import get_files_in_path, copy_file
import logging


logger = logging.getLogger(__name__)


class StaticFileRenderer(Renderer):
    """
    Copies static files to `output_path`
    """
    def get_files_to_copy(self, changed_files: set = None):
        # Return list of tuples: (absolute_original_path, destination_relative_to_output_path)
        return []

    def render(self, context: dict, changed_files: set = None) -> set:
        files_to_keep = set()
        for asset_path, rel_output_path in self.get_files_to_copy():
            abs_output_path = config.output_path / rel_output_path

            if changed_files is None or asset_path in changed_files:
                logger.info('Copying asset %s', str(rel_output_path))
                copy_file(asset_path, abs_output_path)
            files_to_keep.add(asset_path)

        return files_to_keep


class StaticAssetRenderer(StaticFileRenderer):
    """
    Copies static assets in `templates_path` to `output_path`
    """
    ignored_suffixes = ('.jinja', )

    def get_files_to_copy(self, changed_files: set = None):
        return [
            (config.templates_path / f, f)
            for f in get_files_in_path(config.templates_path)
            if f.suffix.lower() not in self.ignored_suffixes
        ]


class ArchiveRenderer(Renderer):
    """
    Copies archives in `content_path` to `output_path`
    """
    included_suffixes = ('.zip', '.rar', '.gz', '.7z')

    def get_assets_to_copy(self, changed_files: set = None):
        return [
            f for f in get_files_in_path(config.content_path)
            if f.suffix.lower() in self.included_suffixes
        ]

    def render(self, context: dict, changed_files: set = None) -> set:
        files_to_keep = set()
        for asset_path in self.get_assets_to_copy():
            abs_output_path = config.output_path / asset_path

            if changed_files is None or config.content_path / asset_path in changed_files:
                logger.info('Copying static entry %s', str(asset_path))
                copy_file(config.content_path / asset_path, abs_output_path)
            files_to_keep.add(asset_path)

        return files_to_keep
