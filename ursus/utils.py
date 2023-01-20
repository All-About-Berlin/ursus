from importlib import import_module
from pathlib import Path
from PIL import Image
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


def make_image_thumbnail(pil_image: Image, max_size, output_path: Path):
    if not output_path.is_absolute():
        raise ValueError(f"output_path {str(output_path)} is relative. It must be absolute.")

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
    width, height = max_size
    doc = fitz.open(pdf_path)
    pixmap = doc[0].get_pixmap(alpha=False)
    thumbnail = Image.frombytes('RGB', [pixmap.width, pixmap.height], pixmap.samples)
    make_image_thumbnail(thumbnail, max_size, output_path)
