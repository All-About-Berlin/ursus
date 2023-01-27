from itertools import filterfalse
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


def is_entry_template(template_path: Path) -> bool:
    return template_path.with_suffix('').stem == 'entry'


def template_can_render_entry(template_path: Path, entry_uri: str) -> bool:
    return entry_uri.startswith(str(template_path.parent) + '/')


class JinjaRenderer(Renderer):
    """
    Renders all .jinja templates in the templates directory, unless their name starts with '_'.
    """
    def __init__(self, config):
        super().__init__(config)
        self.template_environment = Environment(
            loader=FileSystemLoader(self.templates_path),
            extensions=[JsLoaderExtension, ResponsiveImageExtension],
            autoescape=select_autoescape(),
            undefined=StrictUndefined
        )
        self.template_environment.filters['render'] = render_filter
        self.template_environment.filters.update(config.get('jinja_filters', {}))

    def render_template(self, template_path: Path, context: dict, output_path: Path):
        """Returns an entry into a template, and saves it under output_path
        Args:
            template_path (Path): Path to the template to use, relative to output_path.
            context (dict): Context object used to render the template.
            output_path (str): Path of the generated file, relative to the output_path.
        """
        logger.info('Rendering %s', str(output_path))
        output_path = self.output_path / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        template = self.template_environment.get_template(str(template_path))
        template.stream(**context).dump(str(output_path))
        return output_path

    def get_entry_output_path(self, template_path: Path, entry_uri: str) -> Path:
        """Gets the path where the rendered template will be saved
        Args:
            template_path (Path): Template used to render the entry
            entry_uri (str): URI of the entry to render
        Returns:
            Path: Rendered template output path, relative to the output_path.
        """
        output_suffix = template_path.with_suffix('').suffix
        return Path(entry_uri).with_suffix(output_suffix)

    def render_entry(self, template_path: Path, context: dict, entry_uri: str) -> Path:
        """Returns an entry into a template, and saves it under output_path
        Args:
            template_path (Path): Path to the template to use, relative to output_path.
            context (dict): Context object used to render the template.
            entry_uri (str): URI of the entry to render
        Returns:
            Path: Path of the generated file, relative to the output_path.
        """
        specific_context = {
            **context,
            'entry': context['entries'][entry_uri]
        }
        output_path = self.get_entry_output_path(template_path, entry_uri)
        self.render_template(template_path, specific_context, output_path)
        return output_path

    def render(self, context, changed_files=None, fast=False) -> set:
        template_paths = get_files_in_path(self.templates_path, suffix='.jinja')

        render_queue = OrderedSet()

        changed_entry_uris = set()
        changed_templates = set()
        for file in (changed_files or set()):
            if not file.exists():
                continue

            if file.is_relative_to(self.content_path):
                changed_entry_uris.add(str(file.relative_to(self.content_path)))
            elif file.is_relative_to(self.templates_path):
                changed_templates.add(file.relative_to(self.templates_path))

        # Process edited entries
        for entry_uri in changed_entry_uris:
            for tp in template_paths:
                if is_entry_template(tp) and template_can_render_entry(tp, entry_uri):
                    render_queue.add(('entry', tp, entry_uri))

        # Process edited templates
        for template_path in changed_templates:
            if is_entry_template(template_path):
                for entry_uri in context['entries']:
                    if template_can_render_entry(template_path, entry_uri):
                        render_queue.add(('entry', template_path, entry_uri))
            else:
                render_queue.add(('template', template_path, template_path.with_suffix('')))

        # Process everything else
        for template_path in template_paths:
            if is_entry_template(template_path):
                for entry_uri in context['entries']:
                    if template_can_render_entry(template_path, entry_uri):
                        if fast:  # Update mtime to avoid deletion
                            (self.output_path / self.get_entry_output_path(template_path, entry_uri)).touch()
                        else:
                            render_queue.add(('entry', template_path, entry_uri))
            else:
                output_path = template_path.with_suffix('')  # Remove .jinja
                if fast:
                    (self.output_path / output_path).touch()  # Update mtime to avoid deletion
                else:
                    render_queue.add(('template', template_path, output_path))

        for render_type, template_path, value in render_queue:
            if render_type == 'entry':
                self.render_entry(template_path, context, value)
            elif render_type == 'template':
                self.render_template(template_path, context, value)
