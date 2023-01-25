class Renderer:
    def __init__(self, config):
        self.content_path = config['content_path']
        self.templates_path = config['templates_path']
        self.output_path = config['output_path']

    def render(self, context: dict, changed_files: set = None, fast: bool = False):
        """Creates, updates or touches files in output_path

        Args:
            context (dict): Context used to render this file
            changed_files (set, optional): A list of changed content and
                template files (absolute paths)
            fast (bool, optional): If True, prioritize build speed over
                completeness.

        Raises:
            NotImplementedError: Description
        """
        raise NotImplementedError
