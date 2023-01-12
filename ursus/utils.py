from importlib import import_module


def import_class(import_path):
    module_name, class_name = import_path.rsplit('.', 1)
    module = import_module(module_name)
    return getattr(module, class_name)


def import_config(import_path):
    module = import_module(import_path)
    return getattr(module, 'config')
