from importlib import import_module
from pathlib import Path
from PIL import Image
from xml.etree import ElementTree
import fitz
import sys


def import_class(import_path):
    module_name, class_name = import_path.rsplit('.', 1)
    module = import_module(module_name)
    return getattr(module, class_name)


def import_config(module_or_path: str):
    """
    Imports the `config` variable from a Python file or a Python module
    """
    file_path = Path(module_or_path)
    if file_path.exists():
        sys.path.append(str(file_path.parent))
        module = import_module(file_path.with_suffix('').name)
    else:
        module = import_module(module_or_path)

    return getattr(module, 'config')


def is_ignored_file(path: Path, root_path=None):
    """
    True if the file or any of its parents (up to root_path) start with _ or .
    """
    return (
        path.stem.startswith(('_', '.'))
        or any([
            p.stem.startswith(('_', '.'))
            for p in path.relative_to(root_path).parents
        ])
    )


def is_image(path: Path):
    assert path.is_absolute(), 'is_image must be called with an absolute path'

    # Notably missing: .heif, .heic
    image_suffixes = ('.apng', '.avif', '.gif', '.jpg', '.jpeg', '.png', '.svg', '.webp')
    return path.is_file() and path.suffix.lower() in image_suffixes


def is_pdf(path: Path):
    assert path.is_absolute(), 'is_pdf must be called with an absolute path'
    return path.is_file() and path.suffix.lower() == '.pdf'


def is_svg(path: Path):
    assert path.is_absolute(), 'is_svg must be called with an absolute path'
    return path.is_file() and path.suffix.lower() == '.svg'


def get_files_in_path(path: Path, whitelist=None, suffix=None):
    """
    Returns a list of valid, visible files under a given path. If whitelist is set, only files in this list are
    returned. The returned paths are relative to `path`.
    """
    if whitelist:
        files = []
        for f in whitelist:
            if (not f.is_absolute()) and (path / f).exists():
                files.append(f)
            elif f.is_absolute() and f.is_relative_to(path):
                files.append(f.relative_to(path))
    else:
        files = path.rglob('[!._]*' + (suffix or ''))

    return [
        f.relative_to(path) for f in files
        if f.is_file() and not is_ignored_file(f, path)
    ]


def hard_link_file(input_path: Path, output_path: Path):
    assert input_path.is_absolute(), f"input_path {str(input_path)} is relative. It must be absolute."
    assert output_path.is_absolute(), f"output_path {str(output_path)} is relative. It must be absolute."

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.unlink(missing_ok=True)
    output_path.hardlink_to(input_path)


def make_image_thumbnail(pil_image: Image, max_size, output_path: Path):
    assert output_path.is_absolute(), f"output_path {str(output_path)} is relative. It must be absolute."

    pil_image.thumbnail(max_size, Image.ANTIALIAS)
    save_args = {'optimize': True}
    if output_path.suffix.lower() == '.jpg':
        save_args['progressive'] = True
    elif output_path.suffix.lower() == '.webp':
        save_args['exact'] = True

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Note: The saved image is stripped of EXIF data
    pil_image.save(output_path, **save_args)


def make_pdf_thumbnail(pdf_path: Path, max_size, output_path: Path):
    """
    Creates an image preview of a PDF file
    """
    assert output_path.is_absolute(), f"output_path {str(output_path)} is relative. It must be absolute."

    width, height = max_size
    doc = fitz.open(pdf_path)
    pixmap = doc[0].get_pixmap(alpha=False)
    thumbnail = Image.frombytes('RGB', [pixmap.width, pixmap.height], pixmap.samples)
    make_image_thumbnail(thumbnail, max_size, output_path)


def get_image_transforms(original_path: Path, transforms_config: dict):
    """
    Yields a list of image transforms that apply to a file.
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

    for key, transform in transforms_config.items():
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
                    if original_path.suffix.lower() == '.svg':
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


def make_picture_element(original_path: Path, output_path: Path, transforms_config: dict, img_attrs={}, site_url='',):
    """
    Creates a responsive HTML <picture> element
    """
    # Mimetypes with broad support that don't require their own <source> element
    standard_mimetypes = ('image/png', 'image/jpeg', 'image/svg+xml')

    # TODO: SVG? PDF?
    default_src = None

    # Build a list of srcsets grouped by mimetype
    sources_by_mimetype = {}
    for transform in get_image_transforms(original_path, transforms_config):
        width = transform['max_size'][0]
        mimetype = transform['output_mimetype']

        if mimetype.startswith('image/'):
            srcset_part = f"{site_url}/{str(transform['output_path'])} {width}w"
            sources_by_mimetype.setdefault(mimetype, [])
            sources_by_mimetype[mimetype].append(srcset_part)

            if not default_src and mimetype in standard_mimetypes:
                default_src = transform['output_path']

    # Create a <picture> with <source type="" srcset=""> for each mimetype
    picture = ElementTree.Element('picture')
    for mimetype, srcset_elements in sources_by_mimetype.items():
        source = ElementTree.Element('source', attrib={
            'type': mimetype,
            'srcset': ", ".join(srcset_elements)
        })
        picture.append(source)

    # Add an <img> with the default image to the <picture>
    img = ElementTree.Element('img', attrib=img_attrs)
    assert default_src is not None, f"default_src is None for {original_path}"
    if default_src.suffix != '.svg':
        with Image.open(output_path / default_src) as pil_image:
            width, height = pil_image.size
            img.attrib['width'] = str(width)
            img.attrib['height'] = str(height)
    img.attrib['loading'] = 'lazy'
    img.attrib['src'] = str(default_src)

    picture.append(img)

    return picture


def make_figure_element(original_path: Path, output_path: Path, transforms_config: dict, img_attrs={}, a_attrs=None, site_url=''):
    """
    Creates a responsive HTML <figure> element with the image title as <figcaption>. Returns a simple <picture> if there
    is no title.
    """
    image = make_picture_element(original_path, output_path, transforms_config, img_attrs, site_url)
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
    figcaption = ElementTree.Element('figcaption')
    figcaption.text = img_attrs['title']
    figure.append(figcaption)

    return figure
