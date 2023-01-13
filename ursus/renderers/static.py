from . import Renderer
from pathlib import Path
import logging
import shutil


logger = logging.getLogger(__name__)


class StaticAssetRenderer(Renderer):
    """
    Copies static assets in `templates_path` to `output_path`.
    """
    ignored_suffixes = ('.jinja', '')

    def get_assets_to_copy(self):
        def is_ignored(path: Path):
            return (
                path.stem.startswith(('_', '.'))
                or path.suffix in self.ignored_suffixes
                or any([
                    p.stem.startswith(('_', '.'))
                    for p in path.relative_to(self.templates_path).parents
                ])
            )

        return [
            p.relative_to(self.templates_path)
            for p in self.templates_path.rglob('*')
            if p.is_file() and not is_ignored(p)
        ]

    def render(self, full_context):
        for asset_path in self.get_assets_to_copy():
            logger.info('Copying %s', str(asset_path))
            (self.output_path / asset_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(self.templates_path / asset_path, self.output_path / asset_path)
