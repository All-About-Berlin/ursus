from . import Renderer
from pathlib import Path
from PIL import Image
from ursus.utils import get_files_in_path, make_image_thumbnail, make_pdf_thumbnail, is_image, is_pdf, is_svg
import logging


logger = logging.getLogger(__name__)


def get_image_transforms(original_path: Path, sizes_config: dict):
    """
    Yields a list of image transforms that apply to a file.
    """
    for key, transform in sizes_config.items():
        includes = transform.get('include', ['*'])
        includes = [includes] if isinstance(includes, str) else includes

        excludes = transform.get('exclude', [])
        excludes = [excludes] if isinstance(excludes, str) else excludes

        transform_applies_to_file = (
            any(original_path.match(pattern) for pattern in includes)
            and not any(original_path.match(pattern) for pattern in excludes)
        )

        if transform_applies_to_file:
            # Normalise and deduplicate suffixes
            # For orig_image.JPG, ('original', 'jpg') becomes ('.jpg')
            output_suffixes = set([
                original_path.suffix.lower() if t == 'original' else '.' + t
                for t in transform.get('output_types', ['original'])
            ])

            for suffix in output_suffixes:
                if suffix == original_path.suffix.lower():
                    output_image_path = original_path
                else:
                    output_image_path = original_path.with_suffix(suffix)

                yield {
                    **transform,
                    'output_path': output_image_path.parent / key / output_image_path.name,  # It works if key is empty
                    'is_default': key == ''
                }


class ImageTransformRenderer(Renderer):
    """
    Resizes images and generate PDF thumbnails
    """
    def __init__(self, **config):
        super().__init__(**config)
        self.image_transforms = config.get('image_transforms', {})

    def get_files(self, changed_files=None):
        return [
            f for f in get_files_in_path(self.content_path, changed_files)
            if is_image(self.content_path / f) or is_pdf(self.content_path / f)
        ]

    def transform_file(self, input_path: Path, overwrite=False):
        """
        Converts a file to images of preconfigured sizes
        """
        for transform in get_image_transforms(input_path, self.image_transforms):
            output_image_path = self.output_path / transform['output_path']
            max_size = transform['max_size']

            if overwrite or not output_image_path.exists():
                abs_input_path = self.content_path / input_path
                if is_pdf(abs_input_path):
                    if output_image_path.suffix == '.pdf':
                        logger.info('Linking %s to %s', str(input_path), str(transform['output_path']))
                        self.hard_link_file(input_path)
                    else:
                        logger.info('Generating %s preview as %s', str(input_path), str(transform['output_path']))
                        make_pdf_thumbnail(self.content_path / input_path, max_size, output_image_path)
                elif is_svg(abs_input_path):
                    if output_image_path.suffix == '.svg':
                        logger.info('Linking %s to %s', str(input_path), str(transform['output_path']))
                        self.hard_link_file(input_path)
                    else:
                        raise ValueError(f"Can't convert {str(input_path)} to {output_image_path.suffix}")
                else:
                    logger.info('Converting %s to %s', str(input_path), str(transform['output_path']))
                    with Image.open(abs_input_path) as pil_image:
                        make_image_thumbnail(pil_image, max_size, output_image_path)

    def hard_link_file(self, file_path: Path):
        """
        Creates a hard link to a <content_path> file in the <output_path>.

        This is equivalent to copying, but without using extra storage space.
        """
        output_file_path = self.output_path / file_path
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        output_file_path.unlink(missing_ok=True)
        output_file_path.hardlink_to(self.content_path / file_path)

    def render(self, full_context, changed_files=None):
        for file_path in self.get_files(changed_files):
            self.transform_file(file_path, overwrite=False)
