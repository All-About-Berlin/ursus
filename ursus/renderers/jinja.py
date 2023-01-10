from jinja2 import Environment, FileSystemLoader, nodes, pass_context, select_autoescape, TemplateNotFound
from jinja2.ext import Extension
from markupsafe import Markup
from ordered_set import OrderedSet
from pathlib import Path
from . import Renderer
import shutil


class JsLoaderExtension(Extension):
    # a set of names that trigger the extension.
    tags = {"js", "alljs"}

    def __init__(self, environment):
        super().__init__(environment)
        environment.extend(js_fragments=OrderedSet())

    def parse(self, parser):
        token = next(parser.stream)

        if token.test('name:alljs'):
            call = self.call_method('_render_js', args=[nodes.ContextReference()])
            return nodes.Output([nodes.MarkSafe(call)]).set_lineno(token.lineno)
        else:
            body = parser.parse_statements(["name:endjs"], drop_needle=True)
            return nodes.CallBlock(
                self.call_method("_queue_js"), [], [], body
            ).set_lineno(token.lineno)

    def _render_js(self, caller):
        return Markup("".join(self.environment.js_fragments))

    def _queue_js(self, caller):
        self.environment.js_fragments.add(caller())
        return ''


@pass_context
def render_filter(context, value):
    _template = context.eval_ctx.environment.from_string(value)
    result = _template.render(**context)
    return result


class JinjaRenderer(Renderer):
    def __init__(self, **config):
        super().__init__(**config)
        self.template_environment = Environment(
            loader=FileSystemLoader(self.templates_path),
            extensions=[JsLoaderExtension],
            autoescape=select_autoescape()
        )
        self.template_environment.filters['daysAgo'] = lambda x, y: (y - x).days
        self.template_environment.filters['monthsAgo'] = lambda x, y: (y - x).days / 30
        self.template_environment.filters['render'] = render_filter


    def get_page_template(self, page_path: str):
        page_path = Path(page_path)
        potential_templates = []

        # This is an index entry
        if not page_path.suffix:
            potential_templates.append(self.templates_path / page_path / 'index.html')

        # Find an _entry.html template in the parent directories
        potential_templates += [parent_dir / '_entry.html' for parent_dir in page_path.parents]

        try:
            return [
                template_path for template_path in potential_templates
                if (self.templates_path / template_path).exists()
            ][0]
        except IndexError:
            raise TemplateNotFound(potential_templates)

    def _render_template(self, template_path: Path, template_context: dict, output_path: Path):
        output_path = (self.output_path / output_path).with_suffix('.html')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        template = self.template_environment.get_template(str(template_path))
        template.stream(**template_context).dump(str(output_path))

    def render_entry(self, uri: str, full_context: dict):
        if not uri.endswith('.md'):
            return

        output_path = Path(uri).with_suffix('.html')
        template_context = {
            **full_context['globals'],
            'entry': full_context['entries'][uri],
            'entries': full_context['entries'],
        }

        self._render_template(self.get_page_template(uri), template_context, output_path)

    def render_template_file(self, file_path: Path, full_context):
        if file_path.suffix == '.html':
            output_path = file_path.with_suffix('.html')
            template_context = {
                **full_context['globals'],
                'entries': full_context['entries'],
            }
            self._render_template(file_path, template_context, output_path)
        else:
            (self.output_path / file_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(self.templates_path / file_path, self.output_path / file_path)
