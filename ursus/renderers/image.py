from . import Renderer
from pathlib import Path
from PIL import Image
import logging


logger = logging.getLogger(__name__)


# Notably missing: .heif, .heic
image_suffixes = ('.apng', '.avif', '.gif', '.jpg', '.jpeg', '.png', '.svg', '.webp')


def is_image(path: Path):
    return path.is_file() and path.suffix.lower() in image_suffixes


def image_paths_for_sizes(original_image_path: Path, output_image_sizes: dict):
    """
    Given the original image path, get the paths of the different sizes of this image
    """
    for key, size in output_image_sizes.items():
        if key == '':
            output_path = original_image_path.parent / original_image_path.name
            is_default = True
        else:
            output_path = original_image_path.parent / key / original_image_path.name
            is_default = False
        yield size, output_path, is_default


def image_is_resizable(image_path: Path):
    return image_path.suffix != '.svg'


class ImageRenderer(Renderer):
    """
    Resizes images
    """

    def __init__(self, **config):
        super().__init__(**config)
        self.output_image_sizes = config.get('output_image_sizes', {})

    def get_images(self):
        def is_ignored(path: Path):
            return (
                path.stem.startswith(('_', '.'))
                or any([
                    p.stem.startswith(('_', '.'))
                    for p in path.relative_to(self.content_path).parents
                ])
            )

        return [
            p.relative_to(self.content_path)
            for p in self.content_path.rglob('*')
            if is_image(p) and not is_ignored(p)
        ]

    def convert_image(self, image_path: Path, overwrite=False):
        """
        Converts an image image to preconfigured sizes
        """
        to_paths = []
        for max_dimensions, to_path, is_default in image_paths_for_sizes(image_path, self.output_image_sizes):
            to_path = self.output_path / to_path
            if overwrite or not to_path.exists():
                to_path.parent.mkdir(parents=True, exist_ok=True)
                to_paths.append((max_dimensions, to_path))

        for max_dimensions, to_path in to_paths:
            logger.info('Converting %s to %s', str(image_path), str(to_path.relative_to(self.output_path)))
            with Image.open(self.content_path / image_path) as image:
                image.thumbnail(max_dimensions, Image.ANTIALIAS)
                save_args = {'optimize': True}
                if image_path.suffix == '.jpg':
                    save_args['progressive'] = True
                elif image_path.suffix == '.webp':
                    save_args['exact'] = True

                # Note: The saved image is stripped of EXIF data
                image.save(to_path, **save_args)

    def hard_link_image(self, image_path: Path):
        """
        Creates a hard link to a content image in the output directory.

        This is equivalent to copying the image, but without using extra storage space.
        """
        logger.info('Linking %s to %s', str(image_path), str(image_path))
        to_path = self.output_path / image_path
        to_path.unlink(missing_ok=True)
        to_path.hardlink_to(self.content_path / image_path)

    def render(self, full_context):
        for image_path in self.get_images():
            if image_is_resizable(image_path):
                self.convert_image(image_path, overwrite=False)
            else:
                self.hard_link_image(image_path)
