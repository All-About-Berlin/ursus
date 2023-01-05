from importlib import import_module
from pathlib import Path
import logging


logger = logging.getLogger(__name__)


class StaticSiteGenerator:
    """
    Turns a group of files and templates into a static website
    """
    def __init__(self, **config):
        self.content_path = config['content_path']

        self.file_processors = []
        for file_processor_name in config['file_processors']:
            module_name, class_name = file_processor_name.rsplit('.', 1)
            module = import_module(module_name)
            file_processor = getattr(module, class_name)
            self.file_processors.append(file_processor(**config))

    def get_file_processors(self, file_path: Path):
        return [
            file_processor for file_processor in self.file_processors
            if file_processor.should_process(file_path)
        ]

    def get_files(self):
        return [
            f.relative_to(self.content_path)
            for f in self.content_path.rglob('*')
            if f.is_file()
        ]

    def generate(self):
        logging.info("Processing files...")
        for file_path in self.get_files():
            logging.info("Generating page: %s", file_path)
            for file_processor in self.get_file_processors(file_path):
                file_processor.process(file_path)

        logging.info("Done.")
