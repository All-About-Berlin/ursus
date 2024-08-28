# Changelog

## [1.5.0] - 2024-??-??

### Changed

- Log all uncaught exceptions through the default logger.
- Feed `config.logging` to `logging.basicConfig` instead of `coloredlogs` to allow fancier logging configs like multiple log handlers.

### Removed

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