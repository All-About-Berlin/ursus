from pathlib import Path
from ursus.config import config
from ursus.context_processors import Context, ContextProcessor


class StaleEntriesProcessor(ContextProcessor):
    """
    Removes entries if their content file no longer exists
    """

    def process(self, context: Context, changed_files: set[Path] | None = None) -> Context:
        for file in (changed_files or set()):
            if file.is_relative_to(config.content_path) and not file.exists():
                entry_uri = str(file.relative_to(config.content_path))
                try:
                    context['entries'].pop(entry_uri)
                except KeyError:
                    pass

        return context
