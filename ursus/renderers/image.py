from . import Renderer
from PIL import Image
from ursus.config import config
from ursus.utils import make_image_thumbnail, make_pdf_thumbnail, is_pdf, is_svg, copy_file
import logging


logger = logging.getLogger(__name__)


class ImageTransformRenderer(Renderer):
    """
    Resizes images and generate PDF thumbnails
    """
    def __init__(self):
        super().__init__()

    def render(self, context: dict, changed_files: set = None) -> set:
        logger.info("Rendering image transforms...")

        files_to_keep = set()

        for entry_uri, entry in context['entries'].items():
            abs_file_path = config.content_path / entry_uri

            for transform in entry.get('transforms', []):
                output_path = transform['output_path']
                abs_output_path = config.output_path / output_path
                max_size = transform['max_size']

                has_changed = changed_files is None or abs_file_path in changed_files
                if has_changed and not abs_output_path.exists():
                    if is_pdf(abs_file_path):
                        if abs_output_path.suffix.lower() == '.pdf':
                            logger.info('Copying %s to %s', entry_uri, str(output_path))
                            copy_file(abs_file_path, abs_output_path)
                        else:
                            logger.info('Generating %s preview as %s', entry_uri, str(output_path))
                            make_pdf_thumbnail(abs_file_path, max_size, abs_output_path)
                    elif is_svg(abs_file_path):
                        logger.info('Copying %s to %s', entry_uri, str(output_path))
                        copy_file(abs_file_path, abs_output_path)
                    else:
                        logger.info('Converting %s to %s', entry_uri, str(output_path))
                        with Image.open(abs_file_path) as pil_image:
                            make_image_thumbnail(pil_image, max_size, abs_output_path)

                files_to_keep.add(output_path)

        return files_to_keep
