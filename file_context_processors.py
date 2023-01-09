from datetime import datetime
from pathlib import Path
from markdown.extensions import Extension
from markdown.extensions.smarty import SmartyExtension, SubstituteTextPattern
from markdown.extensions.wikilinks import WikiLinkExtension
import markdown


class FileContextProcessor:
    def __init__(self, **config):
        self.content_path = config['content_path']
        self.templates_path = config['templates_path']
        self.output_path = config['output_path']

    def process(self, file_path: Path, entry_context: dict):
        return entry_context


class SmartyPlusExtension(SmartyExtension, Extension):
    """
    The SmartyPants typography extension with a few extra features.
    """
    def educateSectionSign(self, md):
        sectionPattern = SubstituteTextPattern(
            r'§ ', ('§&nbsp;',), md
        )
        self.inlinePatterns.register(sectionPattern, 'smarty-section', 10)

    def educateArrow(self, md):
        arrowPattern = SubstituteTextPattern(
            r' ➞', ('&nbsp;➞',), md
        )
        self.inlinePatterns.register(arrowPattern, 'smarty-arrow', 10)

    def extendMarkdown(self, md):
        super().extendMarkdown(md)
        self.educateSectionSign(md)
        self.educateArrow(md)


class MarkdownContextProcessor(FileContextProcessor):
    def __init__(self, **config):
        super().__init__(**config)
        wikilinks_base_url = config.get('wikilinks_base_url') or config['globals']['site_url']
        self.markdown = markdown.Markdown(extensions=[
            'footnotes',
            'meta',
            'file_context_processors:SmartyPlusExtension',
            WikiLinkExtension(base_url=wikilinks_base_url, end_url='.html')
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
            'url': f"/{str(file_path.with_suffix(''))}",
        })
        return entry_context
