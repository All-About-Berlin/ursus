from . import Renderer
from PIL import Image
from ursus.config import config
from ursus.utils import get_files_in_path, make_image_thumbnail, make_pdf_thumbnail, is_image, is_pdf, is_svg, \
    copy_file, get_image_transforms
import logging


logger = logging.getLogger(__name__)


class ImageTransformRenderer(Renderer):
    """
    Resizes images and generate PDF thumbnails
    """
    def __init__(self):
        super().__init__()

    def get_files_to_transform(self):
        return [
            f for f in get_files_in_path(config.content_path)
            if is_image(config.content_path / f) or is_pdf(config.content_path / f)
        ]

    def render(self, context: dict, changed_files: set = None) -> set:
        logger.info("Rendering image transforms...")

        files_to_keep = set()

        for input_path in self.get_files_to_transform():
            abs_input_path = config.content_path / input_path
            has_changed = changed_files is None or abs_input_path in changed_files

            for transform in get_image_transforms(input_path):
                output_path = transform['output_path']
                abs_output_path = config.output_path / output_path
                max_size = transform['max_size']

                if has_changed and not abs_output_path.exists():
                    if is_pdf(abs_input_path):
                        if abs_output_path.suffix.lower() == '.pdf':
                            logger.info('Copying %s to %s', str(input_path), str(output_path))
                            copy_file(abs_input_path, abs_output_path)
                        else:
                            logger.info('Generating %s preview as %s', str(input_path), str(output_path))
                            make_pdf_thumbnail(config.content_path / input_path, max_size, abs_output_path)
                    elif is_svg(abs_input_path):
                        if abs_output_path.suffix.lower() == '.svg':
                            logger.info('Copying %s to %s', str(input_path), str(output_path))
                            copy_file(abs_input_path, abs_output_path)
                        else:
                            logger.warning(f"Can't convert {str(input_path)} to {abs_output_path.suffix}. Ignoring.")
                            continue
                    else:
                        logger.info('Converting %s to %s', str(input_path), str(output_path))
                        with Image.open(abs_input_path) as pil_image:
                            make_image_thumbnail(pil_image, max_size, abs_output_path)

                files_to_keep.add(output_path)

        return files_to_keep
