from ursus.utils import import_class
from . import Generator
import logging
import time


logger = logging.getLogger(__name__)


class StaticSiteGenerator(Generator):
    """
    Turns a group of files and templates into a static website
    """
    def __init__(self, config):
        super().__init__(config)

        self.templates_path = config['templates_path']
        self.fast_rebuilds = config['fast_rebuilds']

        self.context_processors = [
            import_class(class_name)(config)
            for class_name in config['context_processors']
        ]

        self.renderers = [
            import_class(class_name)(config)
            for class_name in config['renderers']
        ]

        self.context = {
            **config['globals'],
            'config': config,
            'entries': {},
        }

    def get_watched_paths(self):
        return [*super().get_watched_paths(), self.templates_path]

    def generate(self, changed_files: set = None):
        start_time = time.time()

        """
        Build a rendering context from the content
        """
        logger.info("Building context...")
        for context_processor in self.context_processors:
            self.context = context_processor.process(self.context, changed_files)

        """
        Render entries and other templates
        """
        for renderer in self.renderers:
            renderer.render(self.context, changed_files, fast=self.fast_rebuilds)

        """
        Delete output files older than this build. This is how stale output files are deleted.
        """
        if not self.fast_rebuilds:
            for file in self.output_path.rglob('*'):
                if file.is_file() and file.stat().st_mtime < start_time:
                    logger.warning(f"Deleting stale output file {str(file.relative_to(self.output_path))}")
                    file.unlink()

        logger.info("Done.")
