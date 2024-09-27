from pathlib import Path
from typing import Generator
from ursus.renderers.jinja import JinjaRenderer


class MultilingualJinjaRenderer(JinjaRenderer):
    """
    Renders all .jinja templates in the templates directory, unless their name starts with '_'.
    """

    def render_entry(self, template_path: Path, context: dict, entry_uri: str) -> Generator[Path, None, None]:
        specific_context = {
            **context,
            'entry': context['entries'][entry_uri],
            'entry_uri': entry_uri,
        }
        output_path = self.get_entry_output_path(template_path, entry_uri)
        yield self.render_template(template_path, specific_context, output_path)

        for language_code, entry_translation in context['entries'][entry_uri].get('translations', {}).items():
            specific_context = {
                **context,
                'entry': entry_translation,
                'entry_uri': entry_uri,
                'language_code': language_code,
            }
            yield from self.render_template(template_path, specific_context, output_path)
