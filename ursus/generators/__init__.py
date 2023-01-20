from pathlib import Path
from watchdog.events import FileSystemEventHandler
import logging
import threading


logger = logging.getLogger(__name__)


def debounce(wait_time):
    """
    Decorator that will debounce a function so that it is called after wait_time seconds
    If it is called multiple times, will wait for the last call to be debounced and run only this one.
    """
    def decorator(function):
        def debounced(*args, **kwargs):
            def call_function():
                debounced._timer = None
                return function(*args, **kwargs)
            # if we already have a call to the function currently waiting to be executed, reset the timer
            if debounced._timer is not None:
                debounced._timer.cancel()

            # after wait_time, call the function provided to the decorator with its arguments
            debounced._timer = threading.Timer(wait_time, call_function)
            debounced._timer.start()

        debounced._timer = None
        return debounced

    return decorator


class GeneratorObserverEventHandler(FileSystemEventHandler):
    def __init__(self, generator: 'Generator', **kwargs):
        self.generator = generator

        self.queued_changes = None
        self.debounce_timer = None

        return super().__init__(**kwargs)

    def dispatch(self, event):
        if event.event_type in ('created', 'modified', 'moved', 'deleted'):
            self.on_file_change(event)

    def on_file_change(self, event):
        if self.debounce_timer:
            self.debounce_timer.cancel()

        self.debounce_timer = threading.Timer(wait_time, call_function)
        # queue event
        # start or reset timer
        # at end of timer, 
        self.generator.on_file_changes(event.event_type, Path(event.src_path))

    def on_file_changes(self):
        self.on_file_changes(events)


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

    def on_file_changes(self, change_type, file_path: str):
        if file_path.is_file():
            logger.info("File changed: %s", file_path)
            self.generate(changed_files=[file_path])
