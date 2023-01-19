from . import Renderer
from pathlib import Path
from PIL import Image
from ursus.utils import get_files_in_path, make_image_thumbnail, make_pdf_thumbnail
import logging


logger = logging.getLogger(__name__)


# Notably missing: .heif, .heic
image_suffixes = ('.apng', '.avif', '.gif', '.jpg', '.jpeg', '.png', '.svg', '.webp')


def is_image(path: Path):
    assert path.is_absolute(), 'is_image must be called with an absolute path'
    return path.is_file() and path.suffix.lower() in image_suffixes


def is_pdf(path: Path):  # Note: requires an absolute path
    assert path.is_absolute(), 'is_pdf must be called with an absolute path'
    return path.is_file() and path.suffix.lower() == '.pdf'


def image_is_resizable(image_path: Path):
    return image_path.suffix != '.svg'


def get_image_sizes(original_image_path: Path, sizes_config: dict):
    """
    Yields a list of size configs that apply to this image.
    """
    for key, size_config in sizes_config.items():
        includes = size_config.get('include', ['*'])
        includes = [includes] if isinstance(includes, str) else includes

        excludes = size_config.get('exclude', [])
        excludes = [excludes] if isinstance(excludes, str) else excludes

        file_matches_config = (
            any(original_image_path.match(pattern) for pattern in includes)
            and not any(original_image_path.match(pattern) for pattern in excludes)
        )

        if file_matches_config:
            for suffix in size_config.get('output_types', ['original']):
                if suffix == 'original':
                    output_image_path = original_image_path
                else:
                    output_image_path = original_image_path.with_suffix(suffix)

                yield {
                    **size_config,
                    'output_path': output_image_path.parent / key / output_image_path.name,
                    'is_default_size': key == ''
                }


class ImageRenderer(Renderer):
    """
    Resizes images and generate PDF thumbnails
    """
    def __init__(self, **config):
        super().__init__(**config)
        self.image_sizes = config.get('image_sizes', {})

    def get_files(self, changed_files=None):
        return [
            f for f in get_files_in_path(self.content_path, changed_files)
            if (is_image(self.content_path / f) or is_pdf(self.content_path / f))
        ]

    def render_image_sizes(self, file_path: Path, overwrite=False):
        """
        Converts an image or PDF to preconfigured sizes
        """
        output_images_and_sizes = []
        for size_config in get_image_sizes(file_path, self.image_sizes):
            output_image_path = self.output_path / size_config['output_path']
            if overwrite or not output_image_path.exists():
                output_images_and_sizes.append((output_image_path, size_config['max_size']))

        for output_image_path, max_size in output_images_and_sizes:
            logger.info(
                'Converting %s to %s',
                str(file_path), str(output_image_path.relative_to(self.output_path))
            )
            if is_pdf(self.content_path / file_path):
                make_pdf_thumbnail(self.content_path / file_path, max_size, output_image_path)
            else:
                with Image.open(self.content_path / file_path) as pil_image:
                    make_image_thumbnail(pil_image, max_size, output_image_path)

    def hard_link_image(self, image_path: Path):
        """
        Creates a hard link to a content image in the output directory.

        This is equivalent to copying the image, but without using extra storage space.
        """
        logger.info('Linking %s to %s', str(image_path), str(image_path))
        output_image = self.output_path / image_path
        output_image.unlink(missing_ok=True)
        output_image.hardlink_to(self.content_path / image_path)

    def render(self, full_context, changed_files=None):
        for file_path in self.get_files(changed_files):
            if image_is_resizable(file_path):
                self.render_image_sizes(file_path, overwrite=False)
            else:
                self.hard_link_image(file_path)
