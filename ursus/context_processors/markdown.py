from . import Context, EntryContextProcessor, EntryURI
from datetime import datetime
from markdown import Markdown
from markdown.extensions import Extension
from markdown.extensions.footnotes import FootnoteExtension, FN_BACKLINK_TEXT, NBSP_PLACEHOLDER
from markdown.inlinepatterns import SimpleTagPattern
from markdown.postprocessors import RawHtmlPostprocessor
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor
from pathlib import Path
from typing import Any
from ursus.config import config
from ursus.utils import make_figure_element, make_picture_element
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
import logging
import re


logger = logging.getLogger(__name__)


class TaskListProcessor(Treeprocessor):
    box_checked = '[x] '
    box_unchecked = '[ ] '

    def run(self, root: Element) -> Element:
        for li in root.iter(tag='li'):
            text = (li.text or "")

            if text.lower().startswith((self.box_checked, self.box_unchecked)):
                is_checked = text.lower().startswith(self.box_checked)

                checkbox = Element("input", {'type': 'checkbox'})
                if is_checked:
                    checkbox.attrib['checked'] = 'checked'
                if self.md.getConfig('checkbox_class'):
                    checkbox.attrib['class'] = self.md.getConfig('checkbox_class')

                checkbox.tail = text.removeprefix(self.box_checked if is_checked else self.box_unchecked)
                li.text = ''
                li.insert(0, checkbox)
                if self.md.getConfig('list_item_class'):
                    css_classes = set(li.attrib.get('class', '').split())
                    css_classes.update(self.md.getConfig('list_item_class').split())
                    li.attrib['class'] = " ".join(css_classes)

        return root


class TaskListExtension(Extension):
    """
    Adds github-flavored markdown todo lists:

    * [ ] Unchecked item
    * [x] Checked item
    """

    def __init__(self, **kwargs):
        self.config = {
            "list_item_class": ['', 'CSS class to add to the <li> element'],
            "checkbox_class": ['', 'CSS class to add to the checkbox <input>'],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        md.treeprocessors.register(TaskListProcessor(self), "gfm-tasklist", 100)


class JinjaPreprocessor(Preprocessor):
    """
    Ignore Jinja {{ ... }} and {% ... %} tags.
    """
    JINJA_RE = re.compile('({{([^}]+)}})|({%([^}]+)%})', re.MULTILINE | re.DOTALL)

    def run(self, lines: list[str]) -> list[str]:
        text = "\n".join(lines)

        def replace_match(match):
            return self.md.htmlStash.store(match[0])

        return re.sub(self.JINJA_RE, replace_match, text).split("\n")


class JinjaHtmlPostProcessor(RawHtmlPostprocessor):
    """
    Patch RawHtmlPostprocessor to recognize {% ... %} tags as block-level
    elements, and prevent them from being wrapped in a <p> tag.
    """
    JINJA_BLOCK_RE = re.compile('^{%([^}]+)%}$', re.MULTILINE | re.DOTALL)

    def isblocklevel(self, html: str) -> bool:
        m = self.JINJA_BLOCK_RE.match(html)
        if m:
            return True
        return super().isblocklevel(html)


class JinjaExtension(Extension):
    """
    Escape Jinja {% ... %} and {{ ... }} statements in Markdown files.
    """

    def extendMarkdown(self, md):
        md.postprocessors.deregister('raw_html')
        md.preprocessors.register(JinjaPreprocessor(md), 'jinja', 25)
        md.postprocessors.register(JinjaHtmlPostProcessor(md), 'raw_html', 30)


class ResponsiveImageProcessor(Treeprocessor):
    allowed_parents = (
        'a', 'p', 'pre', 'ul', 'ol', 'dl', 'div', 'blockquote', 'noscript', 'section', 'nav', 'article',
        'aside', 'header', 'footer', 'table', 'form', 'fieldset', 'menu', 'canvas', 'details'
    )

    def _swap_element(self, parent: Element, old: Element, new: Element) -> None:
        """
        Replaces `old` element with `new` in `parent` element
        """
        for index, element in enumerate(parent):
            if element == old:
                parent[index] = new
                new.tail = old.tail
                return

    def _upgrade_img(self, img: Element, parents: list[Element]) -> None:
        # Create <picture> with <source> for the different image types and sizes
        # Only apply to local images
        img_src = img.attrib.get('src', '')
        if img_src.startswith('/') or img_src.startswith(config.site_url + '/'):
            image_uri = EntryURI(img_src.removeprefix(config.site_url).removeprefix('/'))

            parent = parents[0]
            grandparent = parents[1]

            def has_single_child(element: Element) -> bool:
                return len(element) == 1 and not element.text

            img_attrs = img.attrib
            a_attrs = None
            image_maker = make_figure_element

            element_to_swap = img
            containing_element = parent

            # A valid <figure> parent with an empty <a> wrapping this <img>
            # In this case, wrap the <figure> around the <a>
            # li > a > img becomes li > figure > a > picture
            if (
                parent.tag == 'a'
                and has_single_child(parent)
                and grandparent.tag in self.allowed_parents
            ):
                a_attrs = parent.attrib
                element_to_swap = parent
                containing_element = grandparent

                # An empty <p> with an empty <a> with this <img>
                # Replace the whole thing with a <figure> containing the <a>
                # p > a > img becomes p > figure > a > picture
                if grandparent.tag == 'p' and has_single_child(grandparent):
                    element_to_swap = grandparent

                    greatgrandparent = parents[2]
                    containing_element = greatgrandparent

            # An empty <p> with this <img>
            # p > img becomes figure > picture
            elif parent.tag == 'p' and has_single_child(parent):
                element_to_swap = parent
                containing_element = grandparent

            # This element does not allow a <figure>. Just use a <picture>.
            elif parent.tag not in self.allowed_parents:
                image_maker = make_picture_element

            image = image_maker(self.md.context, image_uri, img_attrs, a_attrs, sizes=config.image_default_sizes)

            self._swap_element(containing_element, element_to_swap, image)

    def run(self, root: Element) -> None:
        parent_map = {}
        for parent in root.iter():
            for child in parent:
                parent_map[child] = parent

        for img in root.iter('img'):
            child = img
            parents = []
            while parent := parent_map.get(child):
                parents.append(parent)
                child = parent

            self._upgrade_img(img, parents)


class ResponsiveImagesExtension(Extension):
    """
    Transforms how <img> tags are rendered:

    - Adds srcset= to images to make them responsive
    - Wraps block images in a <figure> tag, and replaces the title with a <figcaption>

    """

    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        self.reset()
        md.treeprocessors.register(ResponsiveImageProcessor(md), 'figure', 0)

    def reset(self) -> None:
        pass


class SuperscriptExtension(Extension):
    """
    ^text^ is converted to <sup>text</sup>
    """

    # match ^, at least one character that is not ^, and ^ again
    SUPERSCRIPT_RE = r"(\^)([^\^]+)\2"

    def extendMarkdown(self, md):
        """Insert 'superscript' pattern before 'not_strong' pattern (priority 70)."""

        md.inlinePatterns.register(SimpleTagPattern(self.SUPERSCRIPT_RE, "sup"), 'superscript', 60)


class FootnotesExtension(FootnoteExtension):
    def extendMarkdown(self, md):
        super().extendMarkdown(md)

    def makeFootnotesDiv(self, root: Element) -> Element | None:
        if not list(self.footnotes.keys()):
            return None

        container = Element("details")
        container.set("class", "footnote")
        container.set("id", "footnotes")
        summary = ElementTree.SubElement(container, "summary")
        summary.text = "Sources and footnotes"
        ol = ElementTree.SubElement(container, "ol")

        surrogate_parent = Element("div")

        backlink_title = self.getConfig("BACKLINK_TITLE").replace("%d", "{}")

        for index, id in enumerate(self.footnotes.keys(), start=1):
            li = ElementTree.SubElement(ol, "li")
            li.set("id", self.makeFootnoteId(id))
            # Parse footnote with surrogate parent as li cannot be used.
            # List block handlers have special logic to deal with li.
            # When we are done parsing, we will copy everything over to li.
            self.parser.parseChunk(surrogate_parent, self.footnotes[id])
            for el in list(surrogate_parent):
                li.append(el)
                surrogate_parent.remove(el)
            backlink = Element("a")
            backlink.set("href", f"#{self.makeFootnoteRefId(id)}")
            backlink.set("class", "footnote-backref")
            backlink.set(
                "title",
                backlink_title.format(index)
            )
            backlink.text = FN_BACKLINK_TEXT

            if len(li):
                node = li[-1]
                if node.tag == "p":
                    node.text = node.text + NBSP_PLACEHOLDER
                    node.append(backlink)
                else:
                    p = ElementTree.SubElement(li, "p")
                    p.append(backlink)

        return container


class MarkdownProcessor(EntryContextProcessor):
    def __init__(self):
        super().__init__()

        self.markdown = Markdown(
            output_format='html',
            extensions=list(config.markdown_extensions.keys()),
            extension_configs=config.markdown_extensions,
        )

    def parse_metadata(self, raw_metadata: dict[str, Any]) -> dict[str, Any]:
        metadata = {}
        for key, value in raw_metadata.items():
            if len(value) == 0:
                continue
            if len(value) == 1:
                value = value[0]

            if key.startswith('date_'):
                value = datetime.strptime(value, '%Y-%m-%d').astimezone()

            if key.startswith('related_'):
                if isinstance(value, list):
                    values = list(filter(bool, [v.strip() for v in value]))
                else:
                    values = [v.strip() for v in value.split(',')]
                value = values if len(values) > 1 else values[0]

            metadata[key] = value
        return metadata

    def process_entry(self, context: Context, entry_uri: EntryURI, changed_files: set[Path] | None = None) -> None:
        if entry_uri.lower().endswith('.md'):
            if config.fast_rebuilds and changed_files and (config.content_path / entry_uri) not in changed_files:
                return

            self.markdown.context = context
            markdown_text = (config.content_path / entry_uri).read_text()
            html = self.markdown.reset().convert(markdown_text)

            context['entries'][entry_uri].update({
                **self.parse_metadata(self.markdown.Meta),
                'body': html,
                'table_of_contents': self.markdown.toc_tokens,
                'url': f"{config.site_url}/{str(Path(entry_uri).with_suffix(config.html_url_extension))}",
            })
