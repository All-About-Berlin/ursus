class ContextProcessor:
    def process(self, context: dict, changed_files: set = None) -> dict:
        """Transforms the context and returns it. The context is used to render templates.

        Args:
            context (dict): An object that represents all data used to render templates
                (website info, blog posts, utility functions, etc.)
            changed_files (set, optional): A list of files that changed since the last context update.

        Returns:
            dict: The updated context
        """
        return context


class EntryContextProcessor(ContextProcessor):
    def process(self, context: dict, changed_files: set = None) -> dict:
        for entry_uri in list(context['entries'].keys()):
            self.process_entry(context, entry_uri)
        return context

    def process_entry(self, context: dict, entry_uri: str):
        raise NotImplementedError
