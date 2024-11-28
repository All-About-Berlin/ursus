from pathlib import Path
from ursus.config import config
from watchdog.events import FileSystemEventHandler
import logging
import threading


logger = logging.getLogger(__name__)


class GeneratorObserverEventHandler(FileSystemEventHandler):
    def __init__(self, generator: 'Generator', **kwargs):
        self.generator = generator

        self.queued_events: set = set()
        self.debounce_timer: threading.Timer | None = None

        self.is_rebuilding: bool = False

        return super().__init__(**kwargs)

    def reschedule_rebuild(self) -> None:
        if self.debounce_timer:
            self.debounce_timer.cancel()
        self.debounce_timer = threading.Timer(0.5, self.on_file_changes)
        self.debounce_timer.start()

    def dispatch(self, event) -> None:
        if event.event_type in ('created', 'modified', 'moved', 'deleted'):
            self.queued_events.add(event)
            self.reschedule_rebuild()

    def on_file_changes(self) -> None:
        if self.is_rebuilding:
            self.reschedule_rebuild()
            return

        self.is_rebuilding = True

        changed_files = set(Path(event.src_path) for event in self.queued_events)
        changed_files.update([Path(e.dest_path) for e in self.queued_events if e.event_type == 'moved'])
        self.queued_events.clear()
        if len(changed_files):
            try:
                self.generator.on_file_changes(changed_files)
            except:
                logging.exception("Could not generate site")
        self.is_rebuilding = False


class Generator:
    def generate(self, changed_files: set[Path] | None = None) -> None:
        raise NotImplementedError

    def get_watched_paths(self) -> list[Path]:
        return [config.content_path, ]

    def get_observer_event_handler(self) -> FileSystemEventHandler:
        return GeneratorObserverEventHandler(generator=self)

    def on_file_changes(self, changed_files: set) -> None:
        self.generate(changed_files=changed_files)
