from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import markdown


class JinjaProcessor:
    def __init__(self, **config):
        self.base_url = config['base_url']
        self.content_path = config['content_path']
        self.templates_path = config['templates_path']
        self.output_path = config['output_path']
        self.template_environment = Environment(
            loader=FileSystemLoader(self.templates_path),
            autoescape=select_autoescape()
        )
        self.template_environment.globals = config.get('globals', {})

    def get_page_context(self, page_path: Path):
        page_url_path = page_path.with_suffix('')
        return {
            'pageUrl': f'{self.base_url}/{page_url_path}',
            'pagePath': f'/{page_url_path}',
        }

    def get_page_template_path(self, page_path: Path):
        try:
            return [
                parent_dir / '_entry.html'
                for parent_dir in page_path.parents
                if (self.templates_path / parent_dir / '_entry.html').exists()
            ][0]
        except IndexError:
            raise Exception(f'No template found in {str(self.templates_path)} for {str(page_path)}')

    def should_process(self, file_path: Path):
        return False

    def process(self, page_path: Path):
        output_path = (self.output_path / page_path).with_suffix('.html')
        template_variables = self.get_page_context(page_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        page_template_path = self.get_page_template_path(page_path)
        template = self.template_environment.get_template(str(page_template_path))
        template.stream(**template_variables).dump(str(output_path))


class MarkdownProcessor(JinjaProcessor):
    def __init__(self, **config):
        self.markdown = markdown.Markdown(extensions=['meta'])
        return super().__init__(**config)

    def should_process(self, file_path: Path):
        return file_path.suffix == '.md'

    def get_page_context(self, page_path: Path):
        with (self.content_path / page_path).open(encoding='utf-8') as f:
            html = self.markdown.reset().convert(f.read())
        meta = self.markdown.Meta

        context = super().get_page_context(page_path)
        context.update({
            'entry': {
                'title': meta.get('Title'),
                'description': meta.get('Description'),
                'body': html,
                'date_created': datetime.now(),
                'date_updated': datetime.now(),
                'reviews': [],
            },
        })
        return context
