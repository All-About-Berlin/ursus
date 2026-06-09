# Changelog

## [1.6.0] - 2026-06-09

### Added

- `{% css %}` now works like `{% js %}`: code in `{% css %}` blocks is queued and output exactly once when calling `{% allCss %}`.
- `{% queueJs %}` and `{% queueCss %}` are aliases for `{% js %}` and `{% css %}`.

### Changed

- `JsLoaderExtension` and `CssLoaderExtension` now share a common base class `FragmentLoaderExtension`. Subclasses that override `minify_js()` should rename the method to `minify()`.
- `EntryContextProcessor.process()` and `process_entry()` no longer return the `context` object.
- `ArchiveRenderer` now inherits from `StaticFileRenderer`.

### Fixed

- Fixed removed entry keys staying in the context when rebuilding with `--fast`.

## [1.5.0] - 2026-05-21

### Changed

- Markdown frontmatter now supports full YAML.

### Fixed

- Fixed pyright errors when adding custom attributes to `UrsusConfig`.

## [1.4.6] - 2026-02-22

### Added

- `JinjaRenderer`'s `{% js %}` minifier is easier to override

### Fixed

- `JinjaRenderer` re-renders `.jinja` files that include non-Jinja files

## [1.4.5] - 2026-02-17

### Fixed

- `JinjaRenderer` only renders changed template files if they have the `.jinja` extension.

## [1.4.4] - 2026-02-13

### Added

- `config.jinja_extensions` allows user-defined Jinja extensions

### Changed

- Verify that paths passed to `ursus lint` are valid and relative to `config.content_path`.
- Append the `config.site_url` to Markdown URLs and images when rendering them. In other words, convert relative URLs in Markdown files to absolute URLs in HTML files.

## [1.4.3] - 2025-12-13

### Changed

- Fixed performance issues with watching a large number of templates.
- Removed unused translation code
- Removed `coloredlogs`.

## [1.4.0] - 2024-08-07

### Added

- `RelatedEntriesLinter`, which verifies that related entries exist. It's enabled by default.
- `HeadMatterLinter` to create other linters for head matter.

### Removed

- Head matter no longer supports comma-separated lists:

```markdown
---
Related_posts: this, does, not, work
Related_posts:
    this
    still
    works
---
```

## [1.3.0] - 2024-08-04

### Changed

- Linters now return the exact line and column range of linting errors
- `entry.date_updated` is now timezone-aware

## [1.2.0] - 2024-04-24

### Added

- `config.markdown_extensions` to configure extensions of the markdown renderer. See `ursus/config.py` for usage.

### Removed

- Project-specific markdown extensions: `WrappedTableExtension`, `CurrencyExtension`, `TypographyExtension`
- Markdown-related configs that are now replaced by `config.markdown_extensions`