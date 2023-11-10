from . import EntryContextProcessor
from datetime import datetime
from markdown.extensions import Extension
from markdown.extensions.footnotes import FootnoteExtension, FN_BACKLINK_TEXT, NBSP_PLACEHOLDER
from markdown.extensions.smarty import SubstituteTextPattern
from markdown.extensions.toc import TocExtension, slugify
from markdown.extensions.wikilinks import WikiLinkExtension, build_url
from markdown.inlinepatterns import SimpleTagPattern
from markdown.postprocessors import RawHtmlPostprocessor
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor, InlineProcessor
from markdown.extensions.codehilite import CodeHiliteExtension
from pathlib import Path
from ursus.config import config
from ursus.utils import make_figure_element, make_picture_element
from xml.etree import ElementTree
import logging
import markdown
import re


logger = logging.getLogger(__name__)


class TaskListProcessor(Treeprocessor):
    box_checked = '[x] '
    box_unchecked = '[ ] '

    def run(self, root):
        for li in root.iter(tag='li'):
            text = (li.text or "")

            if text.lower().startswith((self.box_checked, self.box_unchecked)):
                is_checked = text.lower().startswith(self.box_checked)

                checkbox = ElementTree.Element("input", {'type': 'checkbox'})
                if is_checked:
                    checkbox.attrib['checked'] = 'checked'
                if self.md.getConfig('checkbox_class'):
                    checkbox.attrib['class'] = self.md.getConfig('checkbox_class')

                checkbox.tail = li.text.removeprefix(self.box_checked if is_checked else self.box_unchecked)
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


class TypographyExtension(Extension):
    """
    Minor typographic improvements
    """
    def extendMarkdown(self, md):
        inline_processor = InlineProcessor(md)

        sectionPattern = SubstituteTextPattern(r'§ ', ('§&nbsp;',), md)
        inline_processor.inlinePatterns.register(sectionPattern, 'typo-section', 10)

        arrowPattern = SubstituteTextPattern(r' ➞', ('&nbsp;➞',), md)
        inline_processor.inlinePatterns.register(arrowPattern, 'typo-arrow', 10)

        ellipsisPattern = SubstituteTextPattern(r'\.\.\.', ('&hellip;',), md)
        inline_processor.inlinePatterns.register(ellipsisPattern, 'typo-ellipsis', 10)

        ellipsisPattern = SubstituteTextPattern(r' - ', ('&nbsp;–&nbsp;',), md)
        inline_processor.inlinePatterns.register(ellipsisPattern, 'typo-emdash', 10)

        squaredPattern = SubstituteTextPattern(r'\^2\^', ('²',), md)
        inline_processor.inlinePatterns.register(squaredPattern, 'squared', 65)

        cubedPattern = SubstituteTextPattern(r'\^3\^', ('³',), md)
        inline_processor.inlinePatterns.register(cubedPattern, 'cubed', 65)

        md.treeprocessors.register(inline_processor, 'typography', 2)


class JinjaPreprocessor(Preprocessor):
    """
    Ignore Jinja {{ ... }} and {% ... %} tags.
    """
    JINJA_RE = re.compile('({{([^}]+)}})|({%([^}]+)%})', re.MULTILINE | re.DOTALL)

    def run(self, lines):
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

    def isblocklevel(self, html):
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


class JinjaCurrencyPreprocessor(Preprocessor):
    """
    Wraps jinja template variables followed with "€" in a <span class="currency"> tag
    """
    JINJA_RE = re.compile('({{([^}]+)}})€', re.MULTILINE | re.DOTALL)

    def run(self, lines):
        text = "\n".join(lines)

        def replace_match(match):
            placeholder = self.md.htmlStash.store(f'<span class="currency">{match[1]}</span>€')
            return placeholder

        return re.sub(self.JINJA_RE, replace_match, text).split("\n")


class CurrencyExtension(Extension):
    """
    Wraps currency in a <span class="currency"> tag
    """
    def extendMarkdown(self, md):
        inline_processor = InlineProcessor(md)

        # 1,234.56€
        currencyPattern = SubstituteTextPattern(
            r'((\d+(,\d{3})*(\.\d{2})?))€',
            ('<span class="currency">', 1, '</span>€'), md
        )
        inline_processor.inlinePatterns.register(currencyPattern, 'currency', 65)
        md.treeprocessors.register(inline_processor, 'currency', 2)

        md.preprocessors.register(JinjaCurrencyPreprocessor(md), 'jinja-cur', 26)


class ResponsiveImageProcessor(Treeprocessor):
    allowed_parents = (
        'a', 'p', 'pre', 'ul', 'ol', 'dl', 'div', 'blockquote', 'noscript', 'section', 'nav', 'article',
        'aside', 'header', 'footer', 'table', 'form', 'fieldset', 'menu', 'canvas', 'details'
    )

    def _swap_element(self, parent, old, new):
        """
        Replaces `old` element with `new` in `parent` element
        """
        for index, element in enumerate(parent):
            if element == old:
                parent[index] = new
                new.tail = old.tail
                return

    def _upgrade_img(self, img, parents):
        # Create <picture> with <source> for the different image types and sizes
        # Only apply to local images
        img_src = img.attrib.get('src')
        if img_src.startswith('/') or img_src.startswith(config.site_url + '/'):
            image_uri = img_src.removeprefix(config.site_url).removeprefix('/')

            parent = parents[0]
            grandparent = parents[1]

            def has_single_child(element):
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

    def run(self, root):
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

    def reset(self):
        pass


class WrappedTableProcessor(Treeprocessor):
    """
    Wrap tables in a <div> to allow scrollable tables on mobile.
    """
    def wrap_table(self, table, parent):
        wrapper = ElementTree.Element('div', attrib={
            'class': self.md.getConfig('table_wrapper_class')
        })
        wrapper.append(table)

        for index, element in enumerate(parent):
            if element == table:
                parent[index] = wrapper
                wrapper.tail = table.tail
                return

    def run(self, root):
        parent_map = {}
        for parent in root.iter():
            for child in parent:
                parent_map[child] = parent

        for table in root.iter('table'):
            child = table
            parents = []
            while parent := parent_map.get(child):
                parents.append(parent)
                child = parent

            self.wrap_table(table, parents[0])


class WrappedTableExtension(Extension):
    """
    Tables are wrapped in a <div>
    """
    def __init__(self, **kwargs):
        self.config = {
            "table_wrapper_class": ['', 'CSS class to add to the <div> element that wraps the table'],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        if self.getConfig('table_wrapper_class'):
            md.treeprocessors.register(WrappedTableProcessor(self), 'wrappedtable', 0)


class SuperscriptExtension(Extension):
    """
    ^text^ is converted to <sup>text</sup>
    """

    # match ^, at least one character that is not ^, and ^ again
    SUPERSCRIPT_RE = r"(\^)([^\^]+)\2"

    def extendMarkdown(self, md):
        """Insert 'superscript' pattern before 'not_strong' pattern (priority 70)."""

        md.inlinePatterns.register(SimpleTagPattern(self.SUPERSCRIPT_RE, "sup"), 'superscript', 60)


class CustomFootnotesExtension(FootnoteExtension):
    def extendMarkdown(self, md):
        super().extendMarkdown(md)

    def makeFootnotesDiv(self, root):
        if not list(self.footnotes.keys()):
            return None

        container = ElementTree.Element("details")
        container.set("class", "footnote")
        container.set("id", "footnotes")
        summary = ElementTree.SubElement(container, "summary")
        summary.text = "Sources and footnotes"
        ol = ElementTree.SubElement(container, "ol")

        surrogate_parent = ElementTree.Element("div")

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
            backlink = ElementTree.Element("a")
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


def patched_slugify(value, separator, keep_unicode=False):
    return slugify(value.lstrip(' 0123456789'), separator, keep_unicode)


class MarkdownProcessor(EntryContextProcessor):
    def __init__(self):
        super().__init__()

        self.markdown = markdown.Markdown(
            output_format='html',
            extensions=[
                'fenced_code',
                'meta',
                'tables',
                'smarty',
                CodeHiliteExtension(guess_lang=False),
                TocExtension(slugify=patched_slugify),
                CustomFootnotesExtension(BACKLINK_TEXT="⤴"),
                JinjaExtension(),
                SuperscriptExtension(),
                TypographyExtension(),
                CurrencyExtension(),
                ResponsiveImagesExtension(),
                WikiLinkExtension(
                    base_url=config.wikilinks_base_url + '/',
                    end_url=config.wikilinks_url_suffix,
                    build_url=config.wikilinks_url_builder or build_url,
                    html_class=config.wikilinks_html_class,
                ),
                TaskListExtension(
                    list_item_class=config.checkbox_list_item_class,
                    checkbox_class=config.checkbox_list_item_input_class,
                ),
                WrappedTableExtension(
                    table_wrapper_class=config.table_wrapper_class,
                )
            ]
        )

    def _parse_metadata(self, raw_metadata):
        metadata = {}
        for key, value in raw_metadata.items():
            if len(value) == 0:
                continue
            if len(value) == 1:
                value = value[0]

            if key.startswith('date_'):
                value = datetime.strptime(value, '%Y-%m-%d')

            if key.startswith('related_'):
                if type(value) == list:
                    values = list(filter(bool, [v.strip() for v in value]))
                else:
                    values = [v.strip() for v in value.split(',')]
                value = values if len(values) > 1 else values[0]

            metadata[key] = value
        return metadata

    def process_entry(self, context: dict, entry_uri: str):
        if entry_uri.endswith('.md'):
            with (config.content_path / entry_uri).open(encoding='utf-8') as f:
                self.markdown.context = context
                html = self.markdown.reset().convert(f.read())

            context['entries'][entry_uri].update({
                **self._parse_metadata(self.markdown.Meta),
                'body': html,
                'table_of_contents': self.markdown.toc_tokens,
                'url': f"{config.site_url}/{str(Path(entry_uri).with_suffix(config.html_url_extension))}",
            })
