# Changelog

## [Unreleased]

### Added

...

### Changed

...

### Removed

...

## [1.2.0] - 2024-04-24

### Added

- `config.markdown_extensions` to configure extensions of the markdown renderer. See `ursus/config.py` for usage.

### Removed

- Project-specific markdown extensions: `WrappedTableExtension`, `CurrencyExtension`, `TypographyExtension`
- Markdown-related configs that are now replaced by `config.markdown_extensions`