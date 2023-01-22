from datetime import datetime
from pathlib import Path
from markdown.extensions import Extension
from markdown.extensions.smarty import SubstituteTextPattern
from markdown.extensions.footnotes import FootnoteExtension, FN_BACKLINK_TEXT, NBSP_PLACEHOLDER
from markdown.inlinepatterns import SimpleTagPattern
from markdown.treeprocessors import Treeprocessor, InlineProcessor
from mdx_wikilink_plus.mdx_wikilink_plus import WikiLinkPlusExtension
from ursus.utils import make_figure_element, make_picture_element
from xml.etree import ElementTree
from . import FileContextProcessor
import logging
import markdown
import re


logger = logging.getLogger(__name__)


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

        squaredPattern = SubstituteTextPattern(r'\^2\^', ('²',), md)
        inline_processor.inlinePatterns.register(squaredPattern, 'squared', 65)

        cubedPattern = SubstituteTextPattern(r'\^3\^', ('³',), md)
        inline_processor.inlinePatterns.register(cubedPattern, 'cubed', 65)

        md.treeprocessors.register(inline_processor, 'typography', 2)


class JinjaStatementsProcessor(Treeprocessor):
    """
    Escapes Jinja statements like {% include "..." %}
    """
    include_statement_re = re.compile('{\%[ ]*include [^\%]*\%}')

    def run(self, root):
        # Remove the wrapping paragraph tag around {% include %} statements that
        # are on their own line.
        for index, el in enumerate(root):
            if el.tag == 'p' and el.text and self.include_statement_re.match(el.text.strip()):
                if index == 0:
                    root.text = el.text.strip()
                else:
                    root[index - 1].tail = el.text.strip()
                root.remove(el)


class ResponsiveImageProcessor(Treeprocessor):
    allowed_parents = (
        'a', 'p', 'pre', 'ul', 'ol', 'dl', 'div', 'blockquote', 'noscript', 'section', 'nav', 'article',
        'aside', 'header', 'footer', 'table', 'form', 'fieldset', 'menu', 'canvas', 'details'
    )

    def __init__(self, md, image_transforms, output_path: Path, site_url: str):
        self.output_path = output_path
        self.image_transforms = image_transforms
        self.site_url = site_url
        super().__init__(md)

    def _swap_element(self, parent, old, new):
        """
        Replaces `old` element with `new` in `parent` element
        """
        for index, element in enumerate(parent):
            if element == old:
                parent[index] = new
                return

    def _upgrade_img(self, img, parents):
        # Create <picture> with <source> for the different image types and sizes
        # Only apply to local images
        img_src = img.attrib.get('src')
        if img_src.startswith('/') or img_src.startswith(self.site_url + '/'):
            image_path = Path(img_src.removeprefix(self.site_url).removeprefix('/'))

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

            image = image_maker(image_path, self.output_path, self.image_transforms, img_attrs, a_attrs, self.site_url)

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
    def __init__(self, output_path: Path, image_transforms: dict, site_url: str):
        self.output_path = output_path
        self.image_transforms = image_transforms or {}
        self.site_url = site_url or ''

    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        self.reset()
        md.treeprocessors.register(
            ResponsiveImageProcessor(
                md,
                output_path=self.output_path,
                image_transforms=self.image_transforms,
                site_url=self.site_url,
            ),
            'figure', 0
        )

    def reset(self):
        pass


class JinjaStatementsExtension(Extension):
    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        self.reset()
        md.treeprocessors.register(JinjaStatementsProcessor(md), 'includes', 0)

    def reset(self):
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


class CustomFootnotesExtension(FootnoteExtension):
    def extendMarkdown(self, md):
        super().extendMarkdown(md)

    def makeFootnotesDiv(self, root):
        if not list(self.footnotes.keys()):
            return None

        container = ElementTree.Element("div")
        container.set("class", "footnote")
        container.set("id", "footnotes")
        h2 = ElementTree.SubElement(container, "h2")
        h2.text = "Footnotes"
        ol = ElementTree.SubElement(container, "ol")

        surrogate_parent = ElementTree.Element("div")

        backlink_title = self.getConfig("BACKLINK_TITLE")

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


class MarkdownProcessor(FileContextProcessor):
    def __init__(self, **config):
        super().__init__(**config)
        self.site_url = config.get('site_url', '')
        self.html_url_extension = config['html_url_extension']

        self.markdown = markdown.Markdown(extensions=[
            'fenced_code',
            'meta',
            'tables',
            'toc',
            CustomFootnotesExtension(BACKLINK_TEXT="⤴"),
            JinjaStatementsExtension(),
            SuperscriptExtension(),
            TypographyExtension(),
            ResponsiveImagesExtension(
                output_path=config['content_path'],
                image_transforms=config.get('image_transforms'),
                site_url=self.site_url
            ),
            WikiLinkPlusExtension(dict(
                base_url=config.get('wikilinks_base_url', '') + '/',
                url_whitespace='%20',
                html_class=None,
                image_class=None,
            )),
        ])

    def _parse_metadata(self, raw_metadata):
        metadata = {}
        for key, value in raw_metadata.items():
            if len(value) == 0:
                continue
            if len(value) == 1:
                value = value[0]

            if(key.startswith('date_')):
                value = datetime.strptime(value, '%Y-%m-%d')

            if(key.startswith('related_')):
                values = [v.strip() for v in value.split(',')]
                value = values if len(values) > 1 else values[0]

            metadata[key] = value
        return metadata

    def process(self, file_path: Path, entry_context: dict):
        if file_path.suffix.lower() == '.md':
            with (self.content_path / file_path).open(encoding='utf-8') as f:
                html = self.markdown.reset().convert(f.read())

            entry_context.update({
                **self._parse_metadata(self.markdown.Meta),
                'body': html,
                'table_of_contents': self.markdown.toc_tokens,
                'url': f"{self.site_url}/{str(file_path.with_suffix(self.html_url_extension))}",
            })

        return entry_context
