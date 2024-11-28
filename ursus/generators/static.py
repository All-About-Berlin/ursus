from ursus.config import config
from ursus.utils import import_class, get_files_in_path
from . import Generator
import logging


logger = logging.getLogger(__name__)


class StaticSiteGenerator(Generator):
    """
    Turns a group of files and templates into a static website
    """

    def __init__(self):
        super().__init__()

        self.context_processors = [
            import_class(class_name)()
            for class_name in config.context_processors
        ]

        self.renderers = [
            import_class(class_name)()
            for class_name in config.renderers
        ]

        self.context = {
            **config.context_globals,
            'config': config,
            'entries': {},
        }

    def get_watched_paths(self):
        return [*super().get_watched_paths(), config.templates_path]

    def generate(self, changed_files=None):
        """
        Build a rendering context from the content
        """
        if config.fast_rebuilds and changed_files is not None:
            logger.info("Updating context...")
        else:
            logger.info("Building context...")

        for file_path in get_files_in_path(config.content_path, changed_files):
            entry_uri = str(file_path)
            self.context['entries'].setdefault(entry_uri, {
                'entry_uri': entry_uri,
            })

        for context_processor in self.context_processors:
            self.context = context_processor.process(self.context, changed_files)

        """
        Render entries and other templates
        """
        files_to_keep = set()
        for renderer in self.renderers:
            logger.debug(f"Rendering entries with {type(renderer).__name__}")
            files_to_keep.update(renderer.render(self.context, changed_files))

        """
        Delete output files older than this build. This is how stale output files are deleted.
        """
        if not config.fast_rebuilds:
            for file in config.output_path.rglob('*'):
                if file.is_file() and file.relative_to(config.output_path) not in files_to_keep:
                    logger.warning(f"Deleting stale output file {str(file.relative_to(config.output_path))}")
                    file.unlink()

        logger.info("Done.")
