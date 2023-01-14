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
