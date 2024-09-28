from pathlib import Path
from ursus.config import config
from ursus.renderers.jinja import JinjaRenderer


class MultilingualJinjaRenderer(JinjaRenderer):
    def template_can_render_entry(self, template_path: Path, context: dict, entry_uri: str) -> bool:
        original_entry_uri = (
            context['entries'][entry_uri].get('translations', {}).get(config.default_language, {}).get('entry_uri')
        )

        return (
            Path(entry_uri).parent == template_path.parent
            or (original_entry_uri and Path(original_entry_uri).parent == template_path.parent)
        )
