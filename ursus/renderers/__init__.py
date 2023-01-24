class Renderer:
    def __init__(self, config):
        self.content_path = config['content_path']
        self.templates_path = config['templates_path']
        self.output_path = config['output_path']

    def render(self, context: dict, changed_files=None, fast=False):
        """Summary
        Args:
            context (dict):
            changed_files (None, optional): A list of changed content and template files (absolute paths)
            fast (bool, optional): If True, prioritize build speed over completeness.
        """
        pass
