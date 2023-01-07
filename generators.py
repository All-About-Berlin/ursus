from utils import import_class
import logging


logger = logging.getLogger(__name__)


class StaticSiteGenerator:
    """
    Turns a group of files and templates into a static website
    """
    def __init__(self, **config):
        self.content_path = config['content_path']
        self.templates_path = config['templates_path']
        self.output_path = config['output_path']

        self.globals = config['globals']

        self.file_context_processors = [
            import_class(class_name)(**config)
            for class_name in config['file_context_processors']
        ]
        self.context_processors = [
            import_class(class_name)(**config)
            for class_name in config['context_processors']
        ]

        self.renderers = [
            import_class(class_name)(**config)
            for class_name in config['renderers']
        ]

    def get_content_files(self):
        return [
            f.relative_to(self.content_path)
            for f in self.content_path.rglob('[!.]*')
            if f.is_file() and not f.name.startswith('_')
        ]

    def get_template_files(self):
        return [
            f.relative_to(self.templates_path)
            for f in self.templates_path.rglob('[!.]*')
            if f.is_file() and not f.name.startswith('_')
        ]

    def generate(self):
        """
        Build a rendering context from the content
        """
        context = {
            'entries': {},
            'globals': self.globals,
        }
        for file_path in self.get_content_files():
            entry_context = {}
            for file_context_processor in self.file_context_processors:
                entry_context = file_context_processor.process(file_path, entry_context)
            context['entries'][str(file_path)] = entry_context

        for context_processor in self.context_processors:
            context = context_processor.process(context)

        """
        Render entries and other templates
        """
        for renderer in self.renderers:
            for uri in context['entries'].keys():
                renderer.render_entry(uri, context)
            for template_path in self.get_template_files():
                renderer.render_template_file(template_path, context)
