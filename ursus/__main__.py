from importlib import import_module
from config import config
import copy
import logging

logging.basicConfig(**config['logging'])

for generator_name, generator_config in config['generators']:
    module_name, class_name = generator_name.rsplit('.', 1)
    module = import_module(module_name)
    generator = getattr(module, class_name)
    local_config = copy.deepcopy(config)
    local_config.pop('generators')
    local_config.update(generator_config)
    generator(**local_config).generate()
