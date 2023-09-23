from importlib import import_module
from pathlib import Path
from PIL import Image
from typing import Iterator
from ursus.config import config
from xml.etree import ElementTree
import fitz
import imagesize
import logging
import shutil
import sys


log_colors = {
    logging.DEBUG: '',
    logging.INFO: '\033[37m\033[0;100m',
    logging.WARNING: '\033[1;90m\033[43m',
    logging.ERROR: '\033[37m\033[41m',
    logging.CRITICAL: '\033[37m\033[41m',
}


def import_class(import_path):
    module_name, class_name = import_path.rsplit('.', 1)
    module = import_module(module_name)
    return getattr(module, class_name)


def import_module_or_path(module_or_path: str) -> dict:
    """
    Imports a module (path.to.module.class or path/to/module.py)

    Args:
        module_or_path (str): path.to.module, or path/to/module.py
    """
    file_path = Path(module_or_path)
    if file_path.exists():
        sys.path.append(str(file_path.parent))
        return import_module(file_path.with_suffix('').name)
    return import_module(module_or_path)


def is_ignored_file(path: Path, root_path: Path) -> bool:
    """Returns whether a file should be ignored by ursus.
    Args:
        path (Path): Path to the file
        root_path (Path): Root path. The name of parent directories above root_path are not considered.

    Returns:
        bool: True if the file or any of its parents (up to root_path) start with _ or .
    """
    return (
        path.stem.startswith(('_', '.'))
        or any([
            p.stem.startswith(('_', '.'))
            for p in path.relative_to(root_path).parents
        ])
    )


def is_image(path: Path) -> bool:
    """Whether the given path points to an image

    Args:
        path (Path): The path to the file

    Returns:
        bool: Whether this file is an image
    """
    assert path.is_absolute(), 'is_image must be called with an absolute path'

    # Notably missing: .heif, .heic
    image_suffixes = ('.apng', '.avif', '.gif', '.jpg', '.jpeg', '.png', '.svg', '.webp')
    return path.is_file() and path.suffix.lower() in image_suffixes


def is_pdf(path: Path) -> bool:
    """Whether the given path points to a PDF

    Args:
        path (Path): The path to the file

    Returns:
        bool: Whether this file is a PDF
    """
    assert path.is_absolute(), 'is_pdf must be called with an absolute path'
    return path.is_file() and path.suffix.lower() == '.pdf'


def is_svg(path: Path):
    """Whether the given path points to an SVG image

    Args:
        path (Path): The path to the file

    Returns:
        bool: Whether this file is an SVG image
    """
    assert path.is_absolute(), 'is_svg must be called with an absolute path'
    return path.is_file() and path.suffix.lower() == '.svg'


def is_raster_image(path: Path):
    return is_image(path) and not is_svg(path)


def get_image_size(path: Path):
    """
    Args:
        path (Path): The absolute Path to an image
    Returns:
        tuple: The image width and height as a tuple
    """
    try:
        width, height = imagesize.get(path)
        if width == height == -1:
            logging.debug(f"Can't get image size, trying again with Pillow: {path}")
            with Image.open(path) as pil_image:
                width, height = pil_image.size
        return width, height
    except Exception as e:
        raise Exception(f"Invalid image size: {path}") from e


def get_files_in_path(path: Path, whitelist: set = None, suffix: str = None) -> list[Path]:
    """
    Returns a list of valid, visible files under a given path.

    Args:
        path (Path): The path under which to find files
        whitelist (set, optional): Only include files that are part of this whitelist
        suffix (str, optional): Only include files with this suffix
    Returns:
        list[Path]: A list of files in this path
    """
    if whitelist:
        files = []
        for f in whitelist:
            if (not f.is_absolute()) and (path / f).exists():
                files.append(path / f)
            elif f.is_absolute() and f.is_relative_to(path):
                files.append(f)
    else:
        files = path.rglob('[!._]*' + (suffix or ''))

    return [
        f.relative_to(path) for f in files
        if (
            f.is_file()
            and not is_ignored_file(f, path)
            and suffix in (None, f.suffix)
        )
    ]


def copy_file(input_path: Path, output_path: Path):
    """Copies a file

    Args:
        input_path (Path): The absolute path of the file to copy
        output_path (Path): The absolute path of the file destination
    """
    assert input_path.is_absolute(), f"input_path {str(input_path)} is relative. It must be absolute."
    assert output_path.is_absolute(), f"output_path {str(output_path)} is relative. It must be absolute."

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(input_path, output_path)


def make_image_thumbnail(pil_image: Image, max_size, output_path: Path):
    """Creates a thumbnail of an image. Strips EXIF metadata.

    Args:
        pil_image (Image): A Pillow Image object containing the image to resize
        max_size (TYPE): Max width and height of the preview image
        output_path (Path): Path to the resulting preview
    """
    assert output_path.is_absolute(), f"output_path {str(output_path)} is relative. It must be absolute."

    pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
    save_args = {'optimize': True}
    if output_path.suffix.lower() == '.jpg':
        save_args['progressive'] = True
    elif output_path.suffix.lower() == '.webp':
        save_args['exact'] = True

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Note: The saved image is stripped of EXIF data
    pil_image.save(output_path, **save_args)


def make_pdf_thumbnail(pdf_path: Path, max_size, output_path: Path):
    """Creates an image preview of a PDF file

    Args:
        pdf_path (Path): Path to the PDF file to preview
        max_size (TYPE): Max width and height of the preview image
        output_path (Path): Path to the resulting preview
    """
    assert output_path.is_absolute(), f"output_path {str(output_path)} is relative. It must be absolute."

    width, height = max_size
    doc = fitz.open(pdf_path)
    pixmap = doc[0].get_pixmap(alpha=False)
    thumbnail = Image.frombytes('RGB', [pixmap.width, pixmap.height], pixmap.samples)
    make_image_thumbnail(thumbnail, max_size, output_path)


def get_image_transforms(original_path: Path) -> Iterator[dict]:
    """
    Yields a list of image transforms that apply to a file.

    Args:
        original_path (Path): Path of the original file/image to transform, relative to config.content_path

    Yields:
        Iterator[dict]: A list of image transforms that apply to this file.
    """
    suffix_to_mimetype = {
        '.apng': 'image/apng',
        '.avif': 'image/avif',
        '.gif': 'image/avif',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp',
    }

    assert not original_path.is_absolute(), "original_path must be a relative path"

    for key, transform in config.image_transforms.items():
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
                    if is_svg(config.content_path / original_path):
                        # .svg images are not be converted
                        continue

                    output_image_path = original_path.with_suffix(suffix)

                yield {
                    **transform,
                    'is_default': key == '',
                    'input_mimetype': suffix_to_mimetype[original_path.suffix.lower()],
                    'output_mimetype': suffix_to_mimetype[output_image_path.suffix.lower()],
                    'output_path': output_image_path.parent / key / output_image_path.name,  # It works if key is empty
                }


def make_picture_element(context: dict, entry_uri: str, img_attrs={}, sizes=None):
    """
    Creates a responsive HTML <picture> element
    """
    # Mimetypes with broad support that don't require their own <source> element
    standard_mimetypes = ('image/png', 'image/jpeg', 'image/svg+xml')

    # TODO: SVG? PDF?
    default_src = None

    # Build a list of srcsets grouped by mimetype
    sources_by_mimetype = {}
    for transform in context['entries'][entry_uri]['transforms']:
        width = transform['max_size'][0]
        mimetype = transform['output_mimetype']

        if mimetype.startswith('image/'):
            srcset_part = f"{config.site_url}/{str(transform['output_path'])} {width}w"
            sources_by_mimetype.setdefault(mimetype, [])
            sources_by_mimetype[mimetype].append(srcset_part)

            if not default_src and mimetype in standard_mimetypes:
                default_src = transform['output_path']

    # Create a <picture> with <source type="" srcset=""> for each mimetype
    picture = ElementTree.Element('picture')
    for mimetype, srcset_elements in sources_by_mimetype.items():
        source = ElementTree.SubElement(picture, 'source', attrib={
            'type': mimetype,
            'srcset': ", ".join(srcset_elements)
        })
        if sizes:
            source.attrib['sizes'] = sizes

    # Add an <img> with the default image to the <picture>
    img = ElementTree.SubElement(picture, 'img', attrib=img_attrs)
    assert default_src is not None, f"default_src is None for {entry_uri}"
    if 'width' in context['entries'][entry_uri]:
        img.attrib['width'] = str(context['entries'][entry_uri]['width'])
    if 'height' in context['entries'][entry_uri]:
        img.attrib['height'] = str(context['entries'][entry_uri]['height'])
    img.attrib['loading'] = 'lazy'
    img.attrib['src'] = f"{config.site_url}/{str(default_src)}"

    return picture


def make_figure_element(context: dict, entry_uri: str, img_attrs={}, a_attrs=None, sizes=None):
    """
    Creates a responsive HTML <figure> element with the image title as <figcaption>. Returns a simple <picture> if there
    is no title.
    """
    image = make_picture_element(context, entry_uri, img_attrs, sizes=sizes)
    if a_attrs and a_attrs.get('href'):
        a_attrs['target'] = '_blank'
        wrapped_image = ElementTree.Element('a', a_attrs)
        wrapped_image.append(image)
    else:
        wrapped_image = image

    if not img_attrs.get('title'):
        return wrapped_image

    figure = ElementTree.Element('figure')
    figure.append(wrapped_image)

    figcaption = ElementTree.SubElement(figure, 'figcaption')
    figcaption.text = img_attrs['title']

    return figure
