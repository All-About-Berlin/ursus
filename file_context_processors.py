from datetime import datetime
from pathlib import Path
import markdown


class FileContextProcessor:
    def __init__(self, **config):
        self.content_path = config['content_path']
        self.templates_path = config['templates_path']
        self.output_path = config['output_path']

    def process(self, file_path: Path, entry_context: dict):
        return entry_context


class MarkdownContextProcessor(FileContextProcessor):
    def __init__(self, **config):
        super().__init__(**config)
        self.markdown = markdown.Markdown(extensions=['meta'])

    def _parse_metadata(self, raw_metadata):
        metadata = {}
        for key, value in raw_metadata.items():
            if len(value) == 0:
                continue
            if len(value) == 1:
                value = value[0]

            if(key.startswith('date_')):
                value = datetime.strptime(value, '%Y-%m-%d')

            metadata[key] = value
        return metadata

    def process(self, file_path: Path, entry_context: dict):
        if not file_path.suffix == '.md':
            return

        with (self.content_path / file_path).open(encoding='utf-8') as f:
            html = self.markdown.reset().convert(f.read())
        entry_context.update({
            **self._parse_metadata(self.markdown.Meta),
            'body': html,
            'url': f"/{str(file_path.with_suffix(''))}",
        })
        return entry_context
