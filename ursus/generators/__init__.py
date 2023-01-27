from pathlib import Path
from watchdog.events import FileSystemEventHandler
import logging
import threading


logger = logging.getLogger(__name__)


class GeneratorObserverEventHandler(FileSystemEventHandler):
    def __init__(self, generator: 'Generator', **kwargs):
        self.generator = generator

        self.queued_events = set()
        self.debounce_timer = None

        return super().__init__(**kwargs)

    def dispatch(self, event):
        if event.event_type in ('created', 'modified', 'moved', 'deleted'):
            logger.info(f"File {event.event_type}: {event.src_path}")

            if self.debounce_timer:
                self.debounce_timer.cancel()

            self.queued_events.add(event)
            self.debounce_timer = threading.Timer(0.5, self.on_file_changes)
            self.debounce_timer.start()

    def on_file_changes(self):
        changed_files = set(Path(event.src_path) for event in self.queued_events)
        changed_files.update([Path(e.dest_path) for e in self.queued_events if e.event_type == 'moved'])
        self.queued_events.clear()
        self.generator.on_file_changes(changed_files)


class Generator:
    def __init__(self, config):
        self.output_path = config['output_path']
        self.content_path = config['content_path']

    def generate(self, changed_files=None):
        pass

    def get_watched_paths(self):
        return [self.content_path, ]

    def get_observer_event_handler(self):
        return GeneratorObserverEventHandler(generator=self)

    def on_file_changes(self, changed_files: set):
        self.generate(changed_files=changed_files)
