from importlib.resources import files
from subprocess import run, STDOUT
from ursus.utils import import_class, get_files_in_path, log_color, log_color_end
from ursus.config import config
from watchdog.observers import Observer
import logging
import sys
import time


def build(watch_for_changes: bool = False) -> None:
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


def lint(files_to_lint=None, min_level=logging.INFO) -> None:
    """Lints the content for errors"""
    linters = [import_class(linter_path)() for linter_path in config.linters]

    has_errors = False

    if files_to_lint:
        logging.info(f"Linting {', '.join(map(str, files_to_lint))}")

    for file_path in sorted(get_files_in_path(config.content_path, whitelist=files_to_lint)):
        for linter in linters:
            linter_errors = list(linter.lint(file_path))
            for position, message, level in linter_errors:
                if position:
                    line_no, col_start, col_end = position
                else:
                    line_no = 0
                    col_start = 0
                    col_end = 1

                if level >= min_level:
                    has_errors = True
                    if line_no is not None:
                        logging.log(level, f"{log_color(level)}{str(file_path)}:{line_no}:{col_start}-{col_end}{log_color_end()} - {message}")
                    else:
                        logging.log(level, f"{str(file_path)} - {message}")
    sys.exit(1 if has_errors else 0)


def translate() -> None:
    babel_config = files("ursus") / 'babel' / 'pybabel.cfg'
    pot_path = config.translations_path / 'messages.pot'

    if not config.default_language or not config.translation_languages:
        raise Exception("Translations are not configured. You must set config.default_language and config.translation_languages.")

    config.translations_path.mkdir(parents=True, exist_ok=True)
    run(
        [
            'pybabel', 'extract',
            '--ignore-dirs', '.*',  # Prevent files/dirs starting with an underscore from being ignored
            '--mapping', str(babel_config),
            '--output-file', str(pot_path), str(config.templates_path)
        ],
        check=True, stdout=sys.stdout, stderr=STDOUT
    )
    for language_code in set([config.default_language, *config.translation_languages]):
        command = 'update' if (config.translations_path / language_code / 'LC_MESSAGES' / 'messages.po').exists() else 'init'
        run(
            [
                'pybabel', command,
                '--input-file', str(pot_path),
                '--locale', language_code,
                '--output-dir', str(config.translations_path),
            ],
            check=True, stdout=sys.stdout, stderr=STDOUT
        )
    run(
        ['pybabel', 'compile', '--directory', str(config.translations_path)],
        check=True, stdout=sys.stdout, stderr=STDOUT
    )
