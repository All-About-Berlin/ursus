from datetime import datetime
from pathlib import Path
from markdown.extensions import Extension
from markdown.extensions.smarty import SubstituteTextPattern
from markdown.inlinepatterns import SimpleTagPattern
from markdown.treeprocessors import Treeprocessor, InlineProcessor
from mdx_wikilink_plus.mdx_wikilink_plus import WikiLinkPlusExtension
from PIL import Image
from ursus.renderers.image import is_image, get_image_transforms
from . import FileContextProcessor
from xml.etree import ElementTree
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

    def __init__(self, md, image_transforms, images_path: Path, site_url: str):
        self.images_path = images_path
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

    def _set_image_dimensions(self, img):
        """
        Adds width and height attributes to an <img> tag
        """
        src = img.attrib.get('src')

        if src.startswith('/') or src.startswith(self.site_url + '/'):
            image_path = self.images_path / src.removeprefix(self.site_url).removeprefix('/')
            if image_path.exists() and is_image(image_path) and image_path.suffix != '.svg':
                with Image.open(image_path) as pil_image:
                    width, height = pil_image.size
                    img.attrib['width'] = str(width)
                    img.attrib['height'] = str(height)

    def _set_image_srcset(self, img):
        """
        Adds srcset attribute to <img> element
        """
        src = img.attrib.get('src')

        if src.startswith('/') or src.startswith(self.site_url + '/'):
            sources = []
            image_path = Path(src.removeprefix(self.site_url).removeprefix('/'))

            for transform in get_image_transforms(image_path, self.image_transforms):
                width, height = transform['max_size']
                output_url = f"{self.site_url}/{str(transform['output_path'])}"
                sources.append(f"{output_url} {width}w")
                if transform['is_default']:
                    img.attrib['src'] = output_url

            if sources:
                img.attrib['srcset'] = ", ".join(sources)

            if '' not in self.image_transforms:
                logger.warning(
                    "No default image size set in `image_transforms`. "
                    f"This <img> src points to an image that might not be there: {src}"
                )

    def _set_image_lazyload(self, img):
        img.attrib['loading'] = 'lazy'

    def _upgrade_img(self, img, parents):
        self._set_image_dimensions(img)
        self._set_image_srcset(img)
        self._set_image_lazyload(img)

        # Wrap image in <figure> tag, but only if the parent element allows a <figure>
        if parents[0].tag in self.allowed_parents:
            figure = ElementTree.Element('figure')

            # If the parent is a <a>, wrap the <img> inside the <figure> with <a>
            if parents[0].tag == 'a':
                a = ElementTree.Element('a', attrib=parents[0].attrib)
                a.append(img)
                figure.append(a)
            else:
                figure.append(img)

            # Convert the image title= to a <figcaption>
            title = img.attrib.get('title')
            if title:
                figcaption = ElementTree.Element('figcaption')
                figcaption.text = title
                figure.append(figcaption)
                img.attrib.pop('title')

            def elem_has_single_child(element):
                return len(element) == 1 and not element.text

            if parents[0].tag == 'a':
                # A <p> with only this <a><img/></a> as a child.
                if (
                    parents[1].tag == 'p'
                    and elem_has_single_child(parents[0])
                    and elem_has_single_child(parents[1])
                ):
                    self._swap_element(parents[2], parents[1], figure)
                else:
                    return
            elif parents[0].tag == 'p':
                # A <p> with only this <img> as a child.
                if elem_has_single_child(parents[0]):
                    self._swap_element(parents[1], parents[0], figure)
                # A <p> with other things in it
                else:
                    return
            else:
                self._swap_element(parents[0], img, figure)

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
    def __init__(self, images_path: Path, image_transforms: dict, site_url: str):
        self.images_path = images_path
        self.image_transforms = image_transforms or {}
        self.site_url = site_url or ''

    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        self.reset()
        md.treeprocessors.register(
            ResponsiveImageProcessor(
                md,
                images_path=self.images_path,
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


class MarkdownProcessor(FileContextProcessor):
    def __init__(self, **config):
        super().__init__(**config)
        self.html_url_extension = config['html_url_extension']

        self.markdown = markdown.Markdown(extensions=[
            'footnotes',
            'fenced_code',
            'meta',
            'tables',
            'toc',
            JinjaStatementsExtension(),
            TypographyExtension(),
            ResponsiveImagesExtension(
                images_path=config['content_path'],
                image_transforms=config.get('image_transforms'),
                site_url=config.get('site_url')
            ),
            SuperscriptExtension(),
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
                value = [v.strip() for v in value.split(',')]

            metadata[key] = value
        return metadata

    def process(self, file_path: Path, entry_context: dict):
        if file_path.suffix == '.md':
            with (self.content_path / file_path).open(encoding='utf-8') as f:
                html = self.markdown.reset().convert(f.read())

            entry_context.update({
                **self._parse_metadata(self.markdown.Meta),
                'body': html,
                'table_of_contents': self.markdown.toc_tokens,
                'url': f"/{str(file_path.with_suffix(self.html_url_extension))}",
            })

        return entry_context
