from . import ContextProcessor
from collections import UserDict
from hashlib import sha256
from openai import OpenAI
from pathlib import Path
from typing import List, Tuple
from ursus.config import config
from ursus.context_processors.markdown import MarkdownProcessor
from ursus.context_processors.related import RelatedEntryReferenceDict
from ursus.utils import parse_markdown_head_matter, format_markdown_head_matter, get_language_name
import logging
import re
import sys


class MultilingualMarkdownProcessor(MarkdownProcessor):
    """
    MarkdownProcessor that also adds a "translations" attribute with AI-translated
    versions of the entry.
    """

    def split_document(self, text: str) -> Tuple[str, str]:
        """
        Split the document into head matter and body
        """
        head_pattern = r'^---\s*\n(.*?\n)*?---\s*\n'
        if head_match := re.search(head_pattern, text, re.DOTALL):
            head_matter = head_match.group(0)
            body = text[len(head_matter):]
            return head_matter, body
        else:
            return "", text

    def chunk_markdown(self, text: str) -> List[[str, str]]:
        chunks = []
        for line in text.split('\n'):
            if line.startswith('## ') or not chunks:
                chunks.append([
                    line.removeprefix('## ') if line.startswith('## ') else None,
                    ''
                ])

            chunks[-1][1] += (line + '\n')

        return chunks

    def translate_string(self, text: str, language_code: str, cache_path: Path) -> str:
        if not text.strip():
            return text

        stripped_text = text.strip()

        prompt = "\n".join((
            "You are an expert legal translator. You translate texts about German immigration law, and about moving to Germany. Your translation must be as accurate as possible.",
            f"Translate the given texts from English to {get_language_name(language_code)}. You must always follow these translation rules:",
            # "- Prefer translations from the dictionary below.",
            "- Preserve the format, whitespace and punctuation of the original text.",
            "- Prefer gender-neutral terms.",
            "- Always address the reader with the informal form 'Du' with a capital D, not the formal 'Sie'.",
            "- Only return the translated text.",
        ))

        cache_hash = sha256((prompt + stripped_text).encode('utf-8')).hexdigest()
        string_cache_path = cache_path / f"{cache_hash}.txt"

        if string_cache_path.exists():
            return string_cache_path.read_text()
        else:
            preview = stripped_text[0:20].replace('\n', ' ').strip()
            logging.info(f"└── Translating string \"{preview}\" to {get_language_name(language_code)}")
            translation = OpenAI(api_key=config.openai_api_key).chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "assistant", "content": "Input the text to translate. I will only return the translated text."},
                    {"role": "user", "content": stripped_text}
                ],
                n=1,
                temperature=0.2,
            ).choices[0].message.content.strip()
            string_cache_path.parent.mkdir(parents=True, exist_ok=True)
            string_cache_path.write_text(translation)
            return translation

    def translate_head_matter(self, head_matter: str, language_code: str, cache_path: Path) -> str:
        if not head_matter.strip():
            return

        metadata, _ = parse_markdown_head_matter(head_matter.split('\n'))
        translated_metadata = {**metadata}
        for field_name in config.metadata_fields_to_translate:
            if field_name not in metadata:
                continue
            elif len(metadata[field_name]) != 1:
                raise ValueError(f"Field is an array: {field_name}")

            translated_metadata[field_name] = [self.translate_string(metadata[field_name][0], language_code, cache_path), ]

        return format_markdown_head_matter(translated_metadata)

    def translate_body(self, text: str, language_code: str, cache_path: Path) -> str:
        if not text.strip():
            return text

        prompt = "\n".join((
            "You are an expert legal translator for guides written in Markdown. The guides are about German immigration law, and about moving to Germany. Your translation must be as accurate as possible.",
            f"Translate the given Markdown texts from English to {get_language_name(language_code)}. You must always follow these translation rules:",
            "- Preserve the format, whitespace and punctuation of the original text.",
            "- Do not translate German terms.",
            "- Do not translate URLs.",
            "- Do not translate footnote symbols. For example '[^123]'.",
            "- Do not translate any text between {% braces with percent signs %}, {{ double curly braces }} or [[ double square braces ]].",
            "- Prefer simple and straightforward language.",
            # "- Prefer translations from the dictionary below.",
            "- Prefer gender-neutral terms.",
            "- If you use a gender asterisk (Genderstern), always add a backslash in front of it. For example, 'Reader' becomes 'Leser\\*in'.",
            "- Always address the reader with the informal form 'Du' with a capital D, not the formal 'Sie'.",
            "- Only return the translated Markdown. Do not wrap the translation in a code block.",
        ))

        translated_chunks = []
        for chunk_title, chunk_text in self.chunk_markdown(text):
            chunk_hash = sha256((prompt + chunk_text).encode('utf-8')).hexdigest()
            chunk_cache_path = cache_path / f"{chunk_hash}.md"

            if chunk_cache_path.exists():
                translated_chunks.append(chunk_cache_path.read_text())
            else:
                # ChatGPT tends to lose whitespace at the start and end of the text, so we preserve and restore it
                whitespace_before = chunk_text[:len(chunk_text) - len(chunk_text.lstrip())]
                whitespace_after = chunk_text[len(chunk_text.rstrip()):]
                stripped_chunk_text = chunk_text.strip()

                preview = stripped_chunk_text[0:20].replace('\n', ' ').strip()
                logging.info(f"└── Translating chunk \"{preview}\" to {get_language_name(language_code)}")
                translated_chunk = whitespace_before + OpenAI(api_key=config.openai_api_key).chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "system", "content": f"The text to translate is titled \"{chunk_title}\""},
                        {"role": "assistant", "content": "Input the Markdown text to translate. I will only return the translated Markdown."},
                        {"role": "user", "content": stripped_chunk_text}
                    ],
                    n=1,
                    temperature=0.2,
                ).choices[0].message.content.strip() + whitespace_after

                chunk_cache_path.parent.mkdir(parents=True, exist_ok=True)
                chunk_cache_path.write_text(translated_chunk)

                translated_chunks.append(translated_chunk)

        return "".join(translated_chunks)

    def process_entry(self, context: dict, entry_uri: str):
        super().process_entry(context, entry_uri)

        if not (
            config.openai_api_key
            and config.default_language
            and config.translation_languages
            and entry_uri.lower().endswith('.md')
        ):
            return

        self.markdown.context = context

        original_text = (config.content_path / entry_uri).read_text()
        desired_translations = {
            key.removeprefix('translation_'): translation_url
            for key, translation_url in context['entries'][entry_uri].items()
            if key.startswith('translation_')
        }

        translations_dict = {
            config.default_language: entry_uri,
        }

        for language_code, translation_url in desired_translations.items():
            if language_code not in config.translation_languages:
                raise ValueError("Desired translation is not in config.translation_languages")

            translation_uri = str(Path(translation_url).with_suffix('.md'))
            logging.info(f"Translating {entry_uri} to {get_language_name(language_code)} as {translation_uri}")

            head_matter, body = self.split_document(original_text)
            translation_cache_path = config.cache_path / 'translations' / translation_uri

            translated_head_matter = self.translate_head_matter(head_matter, language_code, cache_path=translation_cache_path)
            translated_body = self.translate_body(body, language_code, cache_path=translation_cache_path)
            translated_text = f"{translated_head_matter}\n{translated_body}"
            html = self.markdown.reset().convert(translated_text)

            context['entries'].setdefault(translation_uri, {})
            context['entries'][translation_uri].update({
                **self.parse_metadata(self.markdown.Meta),
                'body': html,
                'table_of_contents': self.markdown.toc_tokens,
                'url': f"{config.site_url}/{str(Path(translation_uri).with_suffix(config.html_url_extension))}",
            })
            translations_dict[language_code] = translation_uri

        if desired_translations:
            for language_code, translation_uri in translations_dict.items():
                # Don't override the language attribute if it's hard-coded in the head matter
                context['entries'][translation_uri]['language'] = language_code
                context['entries'][translation_uri]['translations'] = translations_dict


class MultilingualRelatedEntriesProcessor(ContextProcessor):
    """
    Entry fields that start with related_* return a list of entries, instead of
    a list of entry URIs.

    The multilingual version also applies this to translations
    """

    def process(self, context: dict, changed_files: set = None) -> dict:
        for uri, entry in context['entries'].items():
            if not isinstance(context['entries'][uri], RelatedEntryReferenceDict):
                context['entries'][uri] = RelatedEntryReferenceDict(entry, context['entries'])

                for language_code in context['entries'][uri].get('translations', {}).keys():
                    context['entries'][uri]['translations'][language_code] = RelatedEntryReferenceDict(
                        context['entries'][uri]['translations'][language_code],
                        context['entries']
                    )


class TranslationReferenceDict(UserDict):
    def __init__(self, translations_dict: dict, all_entries: dict):
        self.all_entries = all_entries
        super().__init__(translations_dict)

    def __getitem__(self, key):
        if key in self.data:
            translation_uri = self.data[key]
            try:
                return self.all_entries[translation_uri]
            except KeyError:
                raise ValueError(f"{key} contains invalid value {sys.exc_info()[1]}")
        return super().__getitem__(key)


class TranslationsReferenceProcessor(ContextProcessor):
    """
    context['entries'][uri]['translations']['de'] returns the German entry instead of the Germany entry URI
    """

    def process(self, context: dict, changed_files: set = None) -> dict:
        for uri, entry in context['entries'].items():
            if ('translations' in entry and not isinstance(entry['translations'], TranslationReferenceDict)):
                entry['translations'] = TranslationReferenceDict(entry['translations'], context['entries'])

        return context
