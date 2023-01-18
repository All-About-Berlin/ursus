from importlib import import_module
from pathlib import Path
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
