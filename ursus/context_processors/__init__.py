from pathlib import Path


class ContextProcessor:
    def __init__(self, config):
        pass

    def process(self, context: dict):
        return context


class EntryContextProcessor:
    def __init__(self, config):
        self.content_path = config['content_path']
        self.templates_path = config['templates_path']
        self.output_path = config['output_path']

    def process(self, file_path: Path, entry_context: dict):
        return entry_context
