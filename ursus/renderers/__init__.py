from pathlib import Path


class Renderer:
    def __init__(self, **config):
        self.content_path = config['content_path']
        self.templates_path = config['templates_path']
        self.output_path = config['output_path']

    def render_entry(self, uri: str, full_context: dict):
        pass

    def render_template_file(self, file_path: Path, full_context):
        pass
