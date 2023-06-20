from . import Renderer
from ursus.config import config
from ursus.utils import get_files_in_path
import logging
import sass


logger = logging.getLogger(__name__)


class SassRenderer(Renderer):
    """
    Renders Sass .scss files as .css
    """
    def render(self, context: dict, changed_files: set = None) -> set:
        files_to_keep = set()
        for scss_path in get_files_in_path(config.templates_path, changed_files, suffix='.scss'):
            output_path = scss_path.with_suffix('.css')

            logger.info('Rendering %s', str(output_path))
            with (config.output_path / output_path).open('w') as css_file:
                css_file.write(
                    sass.compile(
                        filename=str(config.templates_path / scss_path),
                        output_style='compressed' if config.minify_css else 'nested',
                        include_paths=[str(config.templates_path)],
                    )
                )
            files_to_keep.add(output_path)

        return files_to_keep
