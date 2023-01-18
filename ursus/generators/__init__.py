from pathlib import Path
from watchdog.events import FileSystemEventHandler
import logging


logger = logging.getLogger(__name__)


class GeneratorObserverEventHandler(FileSystemEventHandler):
    def __init__(self, generator: 'Generator', **kwargs):
        self.generator = generator
        return super().__init__(**kwargs)

    def dispatch(self, event):
        if event.event_type in ('created', 'modified', 'moved', 'deleted'):
            self.on_file_change(event)

    def on_file_change(self, event):
        self.generator.on_file_change(event.event_type, Path(event.src_path))


class Generator:
    def __init__(self, **config):
        self.output_path = config['output_path']
        self.content_path = config['content_path']

    def generate(self, changed_files=None):
        pass

    def get_watched_paths(self):
        return [self.content_path, ]

    def get_observer_event_handler(self):
        return GeneratorObserverEventHandler(generator=self)

    def on_file_change(self, change_type, file_path: str):
        if file_path.is_file():
            logger.info("File changed: %s", file_path)
            self.generate(changed_files=[file_path])
