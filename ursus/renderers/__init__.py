class Renderer:
    def render(self, context: dict, changed_files: set = None) -> set:
        """Creates, updates or touches files in output_path

        Args:
            context (dict): Context used to render this file
            changed_files (set, optional): A list of changed content and
                template files (absolute paths)
        Returns:
            set: List of output files that should be preserved. Files that are
                not preserved by any renderer will marked as stale and deleted.

        Raises:
            NotImplementedError: Description
        """
        raise NotImplementedError
