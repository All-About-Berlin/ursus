from pathlib import Path
from ursus.config import config
from ursus.utils import import_class, get_files_in_path
from watchdog.events import FileSystemEventHandler
import logging
import threading


logger = logging.getLogger(__name__)


class GeneratorObserverEventHandler(FileSystemEventHandler):
    def __init__(self, generator: "StaticSiteGenerator", **kwargs):
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
        if event.event_type in ("created", "modified", "moved", "deleted"):
            self.queued_events.add(event)
            self.reschedule_rebuild()

    def on_file_changes(self) -> None:
        if self.is_rebuilding:
            self.reschedule_rebuild()
            return

        self.is_rebuilding = True
        changed_files = set(Path(event.src_path) for event in self.queued_events)
        changed_files.update(
            [Path(e.dest_path) for e in self.queued_events if e.event_type == "moved"]
        )
        self.queued_events.clear()
        if len(changed_files):
            try:
                self.generator.on_file_changes(changed_files)
            except:
                logging.exception("Could not generate site")
        self.is_rebuilding = False


class StaticSiteGenerator:
    """
    Turns a group of files and templates into a static website
    """

    def __init__(self):
        self.context_processors = [
            import_class(class_name)() for class_name in config.context_processors
        ]
        self.renderers = [import_class(class_name)() for class_name in config.renderers]
        self.context = {
            **config.context_globals,
            "config": config,
            "entries": {},
        }

    def get_watched_paths(self) -> list[Path]:
        return [config.content_path, config.templates_path]

    def get_observer_event_handler(self) -> FileSystemEventHandler:
        return GeneratorObserverEventHandler(generator=self)

    def on_file_changes(self, changed_files: set) -> None:
        self.generate(changed_files=changed_files)

    def generate(self, changed_files=None):
        """
        Build a rendering context from the content
        """
        logger.info("Building context...")

        for file_path in get_files_in_path(config.content_path, changed_files):
            entry_uri = str(file_path)
            self.context["entries"][entry_uri] = {"entry_uri": entry_uri}

        for context_processor in self.context_processors:
            context_processor.process(self.context, changed_files)

        """
        Render entries and other templates
        """
        files_to_keep = set()
        for renderer in self.renderers:
            logger.debug(f"Rendering entries with {type(renderer).__name__}")
            files_to_keep.update(renderer.render(self.context, changed_files))

        """
        Delete output files that are not explicitly part of this build, because they are stale.
        """
        for file in config.output_path.rglob("*"):
            if (
                file.is_file()
                and file.relative_to(config.output_path) not in files_to_keep
            ):
                logger.warning(
                    f"Deleting stale output file {str(file.relative_to(config.output_path))}"
                )
                file.unlink()

        logger.info("Done.")
