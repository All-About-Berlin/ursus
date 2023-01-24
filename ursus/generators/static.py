from ursus.utils import import_class, get_files_in_path
from . import Generator
import logging


logger = logging.getLogger(__name__)


class StaticSiteGenerator(Generator):
    """
    Turns a group of files and templates into a static website
    """
    def __init__(self, config):
        super().__init__(config)

        self.templates_path = config['templates_path']

        self.entry_context_processors = [
            import_class(class_name)(**config)
            for class_name in config['entry_context_processors']
        ]
        self.global_context_processors = [
            import_class(class_name)(**config)
            for class_name in config['global_context_processors']
        ]

        self.renderers = [
            import_class(class_name)(**config)
            for class_name in config['renderers']
        ]

        self.context = {
            **config['globals'],
            'config': config,
            'entries': {},
        }

    def get_watched_paths(self):
        return [*super().get_watched_paths(), self.templates_path]

    def get_content_files(self, changed_files=None):
        return get_files_in_path(self.content_path, changed_files)

    def generate(self, changed_files=None):
        """
        Build a rendering context from the content
        """
        logger.info("Building context...")

        for file_path in self.get_content_files(changed_files):
            entry_context = {}
            for file_context_processor in self.entry_context_processors:
                entry_context = file_context_processor.process(file_path, entry_context)

            self.context['entries'].update({
                str(file_path): entry_context
            })

        for context_processor in self.global_context_processors:
            self.context = context_processor.process(self.context, changed_files)

        """
        Render entries and other templates
        """
        for renderer in self.renderers:
            renderer.render(self.context, changed_files)

        logger.info("Done.")
