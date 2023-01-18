from jinja2 import Environment, FileSystemLoader, nodes, pass_context, select_autoescape
from jinja2.ext import Extension
from markupsafe import Markup
from ordered_set import OrderedSet
from pathlib import Path
from . import Renderer
import logging


logger = logging.getLogger(__name__)


class JsLoaderExtension(Extension):
    """
    Jinja extension. Adds the {% js %} and {% alljs %} tags.

    All javascript code between {% js %} tags is combined and queued for future output.

    {% alljs %} outputs the queued javascript code. The code is included in order of addition. If the same code is queued multiple times, it's only output once.
    """
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
        output = "".join(self.environment.js_fragments)
        self.environment.js_fragments.clear()
        return Markup(output)

    def _queue_js(self, caller):
        self.environment.js_fragments.add(caller())
        return ''


@pass_context
def render_filter(context, value):
    return context.eval_ctx.environment.from_string(value).render(**context)


class JinjaRenderer(Renderer):
    """
    Renders all .jinja templates in the templates directory, unless their name starts with '_'.
    """
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
        self.template_environment.filters.update(config.get('jinja_filters', {}))

    def _render_template(self, template_path: Path, template_context: dict, output_path: Path):
        logger.info('Rendering %s', str(output_path))
        output_path = self.output_path / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        template = self.template_environment.get_template(str(template_path))
        template.stream(**template_context).dump(str(output_path))

    def get_templates_to_render(self, changed_files):
        return [
            p.relative_to(self.templates_path)
            for p in self.templates_path.rglob('[!_]*.jinja') if p.is_file()
        ]

    def render(self, full_context, changed_files=None):
        for template_path in self.get_templates_to_render(changed_files):
            # Render once for every entry in that directory
            if template_path.with_suffix('').stem == 'entry':
                for entry_uri, entry in full_context['entries'][str(template_path.parent)].items():
                    entry_context = {
                        **full_context,
                        'entry': entry
                    }
                    output_suffix = template_path.with_suffix('').suffix
                    output_path = Path(entry_uri).with_suffix(output_suffix)
                    self._render_template(template_path, entry_context, output_path)
            # Render once
            else:
                self._render_template(template_path, full_context, template_path.with_suffix(''))
