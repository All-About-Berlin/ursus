from pathlib import Path
from ursus.config import config
from ursus.context_processors import EntryContextProcessor
from ursus.utils import is_raster_image, get_image_size, get_image_transforms, is_image, is_pdf


class ImageProcessor(EntryContextProcessor):
    def process_entry(self, context: dict, entry_uri: str):
        abs_path = config.content_path / entry_uri
        if is_raster_image(abs_path):
            width, height = get_image_size(abs_path)
            context['entries'][entry_uri].update({
                'width': width,
                'height': height,
            })
        if is_image(abs_path) or is_pdf(abs_path):
            context['entries'][entry_uri].update({
                'transforms': list(get_image_transforms(Path(entry_uri))),
            })
