from . import Renderer
from jinja2 import Environment, FileSystemLoader, nodes, pass_context, select_autoescape, StrictUndefined
from jinja2.exceptions import TemplateSyntaxError
from jinja2.ext import Extension, do
from jinja2.meta import find_referenced_templates
from jinja2_simple_tags import StandaloneTag, ContainerTag
from markdown.serializers import to_html_string
from markupsafe import Markup
from ordered_set import OrderedSet
from pathlib import Path
from rjsmin import jsmin
from rcssmin import cssmin
from ursus.config import config
from ursus.utils import get_files_in_path, make_picture_element, is_ignored_file
import logging
import sass


logger = logging.getLogger(__name__)


class JsLoaderExtension(Extension):
    """
    Jinja extension. Adds the {% js %} and {% alljs %} tags.

    All javascript code between {% js %} tags is combined and queued for future
    output. It's minified if config.minify_js is True.

    {% alljs %} outputs the queued javascript code. The code is included in
    order of addition. If the same code is queued multiple times, it's only
    output once.
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
        output = "\n".join(self.environment.js_fragments)
        if config.minify_js:
            output = jsmin(output)
        self.environment.js_fragments.clear()
        return Markup(output)

    def _queue_js(self, caller):
        self.environment.js_fragments.add(caller())
        return ''


class CssLoaderExtension(ContainerTag):
    """
    Jinja extension. Adds the {% css %} tag.

    All CSS code in {% css %} tags is minified if config.minify_css is True.
    """
    tags = {"css"}
    safe_output = True

    def render(self, caller):
        output = caller()
        if config.minify_css:
            output = cssmin(output)
        return Markup(output)


class ScssLoaderExtension(ContainerTag):
    """
    Jinja extension. Adds the {% scss %} tag.

    All Sass code in {% scss %} tags is converted to CSS.
    It's also minified if config.minify_css is True.
    """
    tags = {"scss"}
    safe_output = True

    def __init__(self, *args, **kwargs):
        self.scss_cache = {}

    def render(self, caller):
        scss_code = caller()
        if scss_code not in self.scss_cache:
            self.scss_cache[scss_code] = Markup(
                sass.compile(
                    string=scss_code,
                    output_style='compressed' if config.minify_css else 'nested',
                    include_paths=[str(config.templates_path)],
                )
            )
        return self.scss_cache[scss_code]


class ResponsiveImageExtension(StandaloneTag):
    """Jinja extension. Adds {% image %} tag.

    Usage: {% image 'relative/path/to/original.jpg' img_class='a_css_class' sizes='(min-width: 600px) 160px, 320px' %}

    This tag is replaced by a responsive <picture> element. The correct image transforms for the given source image are
    used.
    """
    tags = {"image"}
    safe_output = True

    def render(self, image_entry_uri, css_class=None, alt=None, sizes=None):
        img_attrs = {}

        if css_class:
            img_attrs['class'] = css_class
        if alt:
            img_attrs['alt'] = alt

        # Render the same way as Python Markdown does, for consistency
        return to_html_string(make_picture_element(self.context, image_entry_uri, img_attrs, sizes))


@pass_context
def render_filter(context, value):
    return context.eval_ctx.environment.from_string(value).render(**context)


def is_entry_template(template_path: Path) -> bool:
    return template_path.with_suffix('').stem == 'entry'


def template_can_render_entry(template_path: Path, entry_uri: str) -> bool:
    return Path(entry_uri).parent == template_path.parent


class JinjaRenderer(Renderer):
    """
    Renders all .jinja templates in the templates directory, unless their name starts with '_'.
    """
    def __init__(self):
        super().__init__()
        self.template_environment = Environment(
            loader=FileSystemLoader(config.templates_path),
            extensions=[do, JsLoaderExtension, CssLoaderExtension, ScssLoaderExtension, ResponsiveImageExtension],
            autoescape=select_autoescape(),
            undefined=StrictUndefined
        )
        self.template_environment.filters['render'] = render_filter
        self.template_environment.filters.update(config.jinja_filters)

    def get_child_templates(self, template_path: Path):
        dependencies = set()
        with (config.templates_path / template_path).open() as template_file:
            ast = self.template_environment.parse(template_file.read())
        child_template_paths = [Path(t.removeprefix('/')) for t in find_referenced_templates(ast)]
        for child_template_path in child_template_paths:
            dependencies.add(child_template_path)
            dependencies.update(self.get_child_templates(child_template_path))
        return dependencies

    def render_template(self, template_path: Path, context: dict, output_path: Path):
        """Returns an entry into a template, and saves it under output_path
        Args:
            template_path (Path): Path to the template to use, relative to output_path.
            context (dict): Context object used to render the template.
            output_path (str): Path of the generated file, relative to the output_path.
        """
        logger.info('Rendering %s', str(output_path))
        abs_output_path = config.output_path / output_path
        abs_output_path.parent.mkdir(parents=True, exist_ok=True)
        template = self.template_environment.get_template(str(template_path))
        try:
            template.stream(**context).dump(str(abs_output_path))
        except TemplateSyntaxError:
            raise
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
            'entry': context['entries'][entry_uri],
            'entry_uri': entry_uri,
        }
        output_path = self.get_entry_output_path(template_path, entry_uri)
        return self.render_template(template_path, specific_context, output_path)

    def render(self, context: dict, changed_files: set = None) -> set:
        template_paths = get_files_in_path(config.templates_path, suffix='.jinja')

        render_queue = OrderedSet()
        files_to_keep = set()

        changed_entry_uris = set()
        changed_templates = set()
        for file in (changed_files or set()):
            if not (file.exists() and file.is_file()):
                continue

            if file.is_relative_to(config.content_path) and not is_ignored_file(file, config.content_path):
                changed_entry_uris.add(str(file.relative_to(config.content_path)))
            elif file.is_relative_to(config.templates_path):
                changed_templates.add(file.relative_to(config.templates_path))
            else:
                continue

        if changed_files is not None and config.fast_rebuilds:
            # Also rerender templates that depend on the changed templates (_style.css > _layout.html > index.html)
            changed_parent_templates = set()
            for template_path in template_paths:
                dependencies = self.get_child_templates(template_path)
                for changed_template in changed_templates:
                    if changed_template in dependencies:
                        logger.info(f"{template_path} is affected by {changed_template} change")
                        changed_parent_templates.add(template_path)
            changed_templates.update(changed_parent_templates)

        # Process edited entries
        for entry_uri in changed_entry_uris:
            for tp in template_paths:
                if is_entry_template(tp) and template_can_render_entry(tp, entry_uri):
                    render_queue.add(('entry', tp, entry_uri))

        # Process edited templates
        for template_path in changed_templates:
            if is_ignored_file(config.templates_path / template_path, config.templates_path):
                continue
            elif is_entry_template(template_path):
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
                        if config.fast_rebuilds:
                            (config.output_path / self.get_entry_output_path(template_path, entry_uri)).touch()
                        else:
                            render_queue.add(('entry', template_path, entry_uri))
            else:
                output_path = template_path.with_suffix('')  # Remove .jinja
                if config.fast_rebuilds:
                    (config.output_path / output_path).touch()
                else:
                    render_queue.add(('template', template_path, output_path))

        for render_type, template_path, value in render_queue:
            if render_type == 'entry':
                files_to_keep.add(self.render_entry(template_path, context, value))
            elif render_type == 'template':
                files_to_keep.add(self.render_template(template_path, context, value))

        return files_to_keep
