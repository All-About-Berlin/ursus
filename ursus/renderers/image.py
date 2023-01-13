from . import Renderer
from pathlib import Path
from PIL import Image
import logging
import shutil


logger = logging.getLogger(__name__)


class ImageRenderer(Renderer):
    """
    Resizes images
    """

    # Notably missing: .heif, .heic
    image_suffixes = ('.apng', '.avif', '.gif', '.jpg', '.jpeg', '.png', '.svg', '.webp')

    def __init__(self, **config):
        super().__init__(**config)
        self.output_image_sizes = config.get('output_image_sizes', {})

    def get_output_sizes(self, image_path: Path):
        for key, size in self.output_image_sizes.items():
            yield size, image_path.parent / key / image_path.name

    def get_images(self):
        def is_image(path: Path):
            return path.is_file() and path.suffix in self.image_suffixes

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

    def render(self, full_context):
        for image_path in self.get_images():
            # Resize to different sizes
            if image_path.suffix != '.svg':
                for max_dimensions, output_path in self.get_output_sizes(image_path):
                    abs_output_path = self.output_path / output_path
                    if not abs_output_path.exists():
                        abs_output_path.parent.mkdir(parents=True, exist_ok=True)
                        with Image.open(self.content_path / image_path) as image:
                            image.thumbnail(max_dimensions, Image.ANTIALIAS)
                            image.save(abs_output_path)

            # Copy the original
            if not (self.output_path / image_path).exists():
                (self.output_path / image_path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(self.content_path / image_path, self.output_path / image_path)
