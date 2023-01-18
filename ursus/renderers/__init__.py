class Renderer:
    def __init__(self, **config):
        self.content_path = config['content_path']
        self.templates_path = config['templates_path']
        self.output_path = config['output_path']

    def render(self, full_context, changed_files=None):
        pass
