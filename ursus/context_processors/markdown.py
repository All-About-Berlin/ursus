from datetime import datetime
from pathlib import Path
from markdown.extensions import Extension
from markdown.extensions.smarty import SmartyExtension, SubstituteTextPattern
from markdown.extensions.wikilinks import WikiLinkExtension
from markdown.treeprocessors import Treeprocessor, InlineProcessor
from . import FileContextProcessor
from xml.etree import ElementTree
import markdown
import re


class TypographyExtension(SmartyExtension, Extension):
    def extendMarkdown(self, md):
        inline_processor = InlineProcessor(md)

        sectionPattern = SubstituteTextPattern(r'§ ', ('§&nbsp;',), md)
        inline_processor.inlinePatterns.register(sectionPattern, 'typo-section', 10)

        arrowPattern = SubstituteTextPattern(r' ➞', ('&nbsp;➞',), md)
        inline_processor.inlinePatterns.register(arrowPattern, 'typo-arrow', 10)

        ellipsisPattern = SubstituteTextPattern(r'\.\.\.', ('&hellip;',), md)
        inline_processor.inlinePatterns.register(ellipsisPattern, 'typo-ellipsis', 10)

        md.treeprocessors.register(inline_processor, 'typography', 2)


class JinjaStatementsProcessor(Treeprocessor):
    include_statement_re = re.compile('{\%[ ]*include [^\%]*\%}')

    def run(self, doc):
        # Remove the wrapping paragraph tag around {% include %} statements that
        # are on their own line.
        for index, el in enumerate(doc):
            if el.tag == 'p' and el.text and self.include_statement_re.match(el.text.strip()):
                if index == 0:
                    doc.text = el.text.strip()
                else:
                    doc[index - 1].tail = el.text.strip()
                doc.remove(el)


class JinjaStatementsExtension(Extension):
    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        self.reset()
        md.treeprocessors.register(JinjaStatementsProcessor(md), 'includes', 0)

    def reset(self):
        pass


class MarkdownProcessor(FileContextProcessor):
    def __init__(self, **config):
        super().__init__(**config)
        wikilinks_base_url = config.get('wikilinks_base_url') or config['globals']['site_url']
        self.html_url_extension = config['html_url_extension']
        self.markdown = markdown.Markdown(extensions=[
            'footnotes',
            'fenced_code',
            'meta',
            'tables',
            JinjaStatementsExtension(),
            TypographyExtension(),
            WikiLinkExtension(base_url=wikilinks_base_url, end_url=self.html_url_extension)
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
        if not file_path.suffix == '.md':
            return

        with (self.content_path / file_path).open(encoding='utf-8') as f:
            html = self.markdown.reset().convert(f.read())
        entry_context.update({
            **self._parse_metadata(self.markdown.Meta),
            'body': html,
            'url': f"/{str(file_path.with_suffix(self.html_url_extension))}",
        })
        return entry_context
