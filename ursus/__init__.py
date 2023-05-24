from ursus.utils import import_class, get_files_in_path, log_colors
from ursus.config import config
from watchdog.observers import Observer
import logging
import time


def build(watch_for_changes: bool = False):
    """Runs ursus and builds a static website

    Args:
        watch_for_changes (bool, optional): Keep running, and rebuild when content or templates change
    """
    generator = import_class(config.generator)()

    if watch_for_changes:
        observer = Observer()

        try:
            generator.generate()
        except:
            logging.exception("Could not generate site")

        for path in generator.get_watched_paths():
            observer.schedule(generator.get_observer_event_handler(), path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        finally:
            observer.stop()
            observer.join()
    else:
        generator.generate()


def lint(files_to_lint=None):
    """Lints the content for errors"""
    linters = [import_class(linter_path)() for linter_path in config.linters]

    for file_path in sorted(get_files_in_path(config.content_path, whitelist=files_to_lint)):
        logging.info(f"\033[1mLinting {str(file_path)}\033[0m")
        for linter in linters:
            for line_no, message, level in linter.lint(file_path):
                if line_no:
                    logging.log(level, f"{log_colors[level]}:{line_no}\033[0m {message}")
                else:
                    logging.log(level, f"{message}")
