from . import Renderer
from pathlib import Path
from ursus.utils import get_files_in_path
import logging
import shutil


logger = logging.getLogger(__name__)


class StaticAssetRenderer(Renderer):
    """
    Copies static assets in `templates_path` to `output_path`.
    """
    ignored_suffixes = ('.jinja', )

    def get_assets_to_copy(self, changed_files=None):
        def has_changed(path: Path):
            if (self.output_path / path).exists():
                return (self.templates_path / path).stat().st_mtime > (self.output_path / path).stat().st_mtime
            else:
                return True

        return [
            f for f in get_files_in_path(self.templates_path, changed_files)
            if has_changed(f) and f.suffix not in self.ignored_suffixes
        ]

    def render(self, full_context, changed_files=None):
        for asset_path in self.get_assets_to_copy(changed_files):
            logger.info('Copying %s', str(asset_path))
            (self.output_path / asset_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(self.templates_path / asset_path, self.output_path / asset_path)
