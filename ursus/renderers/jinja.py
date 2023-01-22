from jinja2 import Environment, FileSystemLoader, nodes, pass_context, select_autoescape, StrictUndefined
from jinja2.ext import Extension
from markupsafe import Markup
from ordered_set import OrderedSet
from pathlib import Path
from ursus.utils import get_files_in_path, make_picture_element
from xml.etree import ElementTree
from . import Renderer
import logging


logger = logging.getLogger(__name__)


class JsLoaderExtension(Extension):
    """
    Jinja extension. Adds the {% js %} and {% alljs %} tags.

    All javascript code between {% js %} tags is combined and queued for future output.

    {% alljs %} outputs the queued javascript code. The code is included in order of addition. If the same code is
    queued multiple times, it's only output once.
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


class ResponsiveImageExtension(Extension):
    """Jinja extension. Adds {% image 'relative/path/to/original.jpg' %} tag.

    This tag is replaced by a responsive <picture> element. The correct image transforms for the given source image are
    used.
    """
    tags = {"image"}

    def __init__(self, environment):
        super().__init__(environment)
        environment.extend(js_fragments=OrderedSet())

    def parse(self, parser):
        token = next(parser.stream)

        args = [parser.parse_expression()]

        if parser.stream.skip_if("comma"):
            args.append(parser.parse_expression())
        else:
            args.append(nodes.Const(None))

        call = self.call_method('_render_image', args)
        return nodes.Output([nodes.MarkSafe(call)]).set_lineno(token.lineno)

    @pass_context
    def _render_image(self, context, image_path, image_class):
        img_attrs = {'class': image_class} if image_class else {}
        output = make_picture_element(
            original_path=Path(image_path),
            output_path=context['config']['output_path'],
            transforms_config=context['config']['image_transforms'],
            site_url=context['config']['site_url'],
            img_attrs=img_attrs,
        )
        return Markup(ElementTree.tostring(output, encoding='unicode'))


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
            extensions=[JsLoaderExtension, ResponsiveImageExtension],
            autoescape=select_autoescape(),
            undefined=StrictUndefined
        )
        self.template_environment.filters['render'] = render_filter
        self.template_environment.filters.update(config.get('jinja_filters', {}))

    def render_template(self, template_path: Path, template_context: dict, output_path: Path):
        logger.info('Rendering %s', str(output_path))
        output_path = self.output_path / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        template = self.template_environment.get_template(str(template_path))
        template.stream(**template_context).dump(str(output_path))

    def render_entry(self, template_path: Path, full_context: dict, entry_uri: str):
        """
        Renders an Entry into a template
        """
        context = {
            **full_context,
            'entry': full_context['entries'][entry_uri]
        }
        output_suffix = template_path.with_suffix('').suffix
        output_path = Path(entry_uri).with_suffix(output_suffix)
        self.render_template(template_path, context, output_path)

    def render(self, full_context, changed_files=None):
        template_paths = get_files_in_path(self.templates_path, suffix='.jinja')

        edited_entry_uris = {
            str(f.relative_to(self.content_path))
            for f in (changed_files or [])
            if f.is_relative_to(self.content_path)
        }

        # First pass: entry.*.jinja templates for entries that were edited
        if edited_entry_uris:
            for template_path in template_paths:
                if template_path.with_suffix('').stem == 'entry':
                    for entry_uri in edited_entry_uris:
                        if entry_uri.startswith(str(template_path.parent) + '/'):
                            self.render_entry(template_path, full_context, entry_uri)

        # Second pass: all other templates
        for template_path in template_paths:
            # Same template, rendered for multiple entries
            if template_path.with_suffix('').stem == 'entry':
                for entry_uri in full_context['entries'][str(template_path.parent)].keys():
                    if entry_uri not in edited_entry_uris:
                        self.render_entry(template_path, full_context, entry_uri)
            # Render once
            else:
                self.render_template(template_path, full_context, template_path.with_suffix(''))
