class Renderer:
    def render(self, context: dict, changed_files: set = None):
        """Creates, updates or touches files in output_path

        Args:
            context (dict): Context used to render this file
            changed_files (set, optional): A list of changed content and
                template files (absolute paths)

        Raises:
            NotImplementedError: Description
        """
        raise NotImplementedError
