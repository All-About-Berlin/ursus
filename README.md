# Ursus

Static site generator used by [All About Berlin](https://allaboutberlin.com). It turns Markdown files and [Jinja](https://jinja.palletsprojects.com/) templates into a static website.

This project is in active use and development.

## Features

Ursus allows **relationships between objects**, not just categories and tags.

It supports **including templates in your content** with the Jinja `{% include %}` tag. This is how I embed calculators in the guides on All About Berlin.

It supports **variables in your content** with the jinja `{{ your_variable }}` tag. This is how I keep values updated across all the content on All About Berlin.

It uses [Python Markdown](https://python-markdown.github.io/extensions/) to process markdown. You can create your own Python extensions, and use the ones supplied with Ursus.

It uses [Jinja](https://jinja.palletsprojects.com/) to render templates, but you can use your own template renderer instead. You can create your own Jinja extensions, and use the ones supplied with Ursus.

It converts images to different sizes and formats, and generates previews for PDFs. The image sizes and formats are configurable.

## Basic concepts

### Content and Entries

**Content** is what fills your website: text, images, videos, PDFs. A single piece of content is called an **Entry**. The location of the Content is set by the `content_path` config parameter. By default, it's under `./content`. You can change that in your config.

Content is usually *rendered* to create a working website. Some content (like Markdown files) is rendered with Templates, and other (like images) is converted to a different file format.

### Templates

**Templates** are used to render your Content. They are the theme of your website. The same templates can be applied to different Entries, or even reused for a different website. They are kept in a separate directory.

The location of the Templates is set by the `templates_path` config parameter. By default, it's under `./templates`. You can have a different `templates_path` for each Generator.

For example:

- HTML templates that wrap a nice theme around your Content.
- Images and other static assets that are part of the website's theme

### Output

This is the final product created by Ursus. By default, the Output is a static website. You can configure Ursus to produce different types of Outputs in different locations.

The location of the Output is set by the `output_path` config parameter. By default, it's under `./output`. You can have a different `output_path` for each Generator.

## How Ursus works

ContextProcessors transform the context, which is a dict with information about each of your Entries. Renderers use the context to know which pages to create, and what content to put in the templates.

### Generators

A **Generator** takes your Content and your Templates and produces an Output. It's a recipe to turn your content into a final result. The default **StaticSiteGenerator** generates a static website. You can write your own Generator to output an eBook, a PDF, or anything else.

#### StaticSiteGenerator

Generates a static website.

### Context processors

The context is a big object that is used to render templates.

A **ContextProcessor** fills this object or transforms its existing content.

For example, the **MarkdownProcessor** generates context out of a markdown file. Take this example markdown file:

```markdown
---
Title: Hello world!
Description: This is an example page
Date_created: 2022-10-10
Date_updated: 2023-01-01
Related_posts: posts/foo.md, posts/bar.md
---

## Hello beautiful world

*This* is a template
```

The `MarkdownProcessor` generates a context object that looks like this:

```
{
    # Information about this entry
    'entry' {
        'title': 'Hello world!',
        'description': 'This is an example page',
        'body': 'This is the content of your markdown file, rendered to HTML',
        'date_created': datetime.datetime(2022, 10, 10, 0, 0, 0, 0)
        'date_updated': datetime.datetime(2023, 1, 1, 0, 0, 0, 0)
        'related_posts': [
            {'title': 'Foo!', ...},
            {'title': 'Bar!', ...}
        ],
        'url': 'https://example.com/posts/hello-world.html',
    },

    # A list of all entries
    'entries': {
        'posts/hello-world.md': {...},
        'posts/foo.md': {...},
        'posts/bar.md': {...},
        'index.md': {...},
        'contact.md': {...},
        'images/example.png': {...},
    },

    # This variable comes from the "context_globals" section of your config. It's an
    # example. You can set your own.
    'twitter_profile_url': 'https://twitter.com/aboutberlin',
}
```

Then, a Renderer can use this information to render a template into a fully working HTML page.

`EntryContextProcessor`s create or transform the context for an individual Entry. For example, the `MarkdownProcessor` above.

`ContextProcessor`s transform the global context after all Entries are processed. For example, it can add a `related_content` field to your blog posts.

Only Entries with matching ContextProcessors are rendered. Entry or directory names that start with `.` or `_` are not rendered. You can use this to create drafts.

#### MarkdownProcessor

The `MarkdownProcessor` creates context for all `.md` files in `content_path`.

It makes a few changes to the default markdown output:

- Lazyload images (`loading=lazy`)
- Convert images to `<figure>` tags when appropriate
- Jinja tags (`{{ ... }}` and `{% ... %}`) are rendered as-is. You can use the, to `{% include %}` template parts and `{{ variables }}` in your content.
- Set the `srcset` to load responsive images from the `image_transforms` config.
- Put the front matter in the context
    - `Related_*` keys are replaced by a list of related entry dicts
    - `Date_` keys are converted to `datetime` objects

#### GetEntriesProcessor

The `GetEntriesProcessor` adds a `get_entries` method to the context. It's used to get a list of entries of a certain type, and sort it.

```jinja
{% set posts = get_entries('posts', sort_by='date_created', reverse=True) %}
```

### Renderers

**Renderer**s create content that make up the Output. In other words, they turn your content files into pages, correctly-sized images, RSS feeds, etc.

#### ImageTransformRenderer

Renders images in `content_path` with a few changes:

- Images are compressed and optimized.
- Images are resized according to the `image_transforms`. The images are shrunk if needed, but never stretched.
- Files that can't be transformed (PDF to PDF) are copied as-is to the output directory.
- Images that can't be resized (SVG to anything) are copied as-is to the output directory.
- Image EXIF data is removed.

This renderer does nothing unless `image_transforms` is set:
```python
config = {
    # ...
    'image_transforms': {
        # Default transform used as <img> src
        # Saved as <output_path>/path/to/image.jpg
        '': {
            'max_size': (3200, 4800),
        },
        # Saved as <output_path>/path/to/image.jpg and .webp
        'thumbnails': {
            'exclude': ('*.pdf', '*.svg'),  # glob patterns
            'max_size': (400, 400),
            'output_types': ('original', 'webp'),
        },
        # Only previews PDF files in specific locations
        # Saved as <output_path>/path/to/image.webp and .png
        'pdfPreviews': {
            'include': ('documents/*.pdf', 'forms/*.pdf'),  # glob patterns
            'max_size': (300, 500),
            'output_types': ('webp', 'png'),
        }
    },
    # ...
}
```

#### JinjaRenderer

Renders Content into Jinja templates using the context made by ContextProcessors.

A Template called `<output_path>/hello-world.html.jinja` will be rendered as `<output_path>/hello-world.html`. The template has access to anything you put in the context, including the `entries` dict, and the `get_entries` method.

A Template called `<output_path>/posts/entry.html.jinja` will render all Entries under `<content_path>/posts/*.md` and save them under `<output_path>/posts/*.html`. The template has access to an `entry` variable.

Only Templates with the `.jinja` extension are rendered. Files or directory names that start with `.` or `_` are not rendered.

Files named `_entry.*.jinja` are rendered once for each Entry with the same path. For example, `<templates_path>/posts/_entry.html.jinja` will render `<content_path>/posts/hello-world.md`, `<content_path>/posts/foo.md` and `<content_path>/posts/bar.md`. The output path is the entry name with the extension replaced. If `<templates_path>/posts/_entry.html.jinja` renders `<templates_path>/posts/hello-world.md`, the output file is `<output_path>/posts/hello-world.html`.

All template files with the `.jinja` extension will be rendered. For example, `<templates_path>/posts/index.html.jinja` will be rendered as `<output_path>/posts/index.html`. Files starting with `_` are ignored.

The output path is the template name without the `.jinja` extension. For example, `index.html.jinja` will be rendered as `index.html`.

#### StaticAssetRenderer

Simply copies static assets (CSS, JS, images, etc.) under `templates_path` to the same subdirectory in `output_path`. Files starting with `.` are ignored. Files and directories starting with `_` are ignored.

It uses hard links instead of copying files. It's faster and it saves space.

## Getting started

1. **Create a directory** for your project. This is a sensible structure, because it works automatically with the default configuration:
    ```
    example_site/
    ├── ursus_config.py  # By default, Ursus will use this config file
    ├── templates/  # By default, Ursus will use this templates directory
    │   ├── index.html.jinja
    │   ├── css/
    │   │   └──style.css
    │   ├── js/
    │   │   └──scripts.js
    │   ├── fonts/
    │   │   ├── open-sans.svg
    │   │   ├── open-sans.ttf
    │   │   └── open-sans.woff
    │   └── posts/
    │       ├── index.html.jinja
    │       └── entry.html.jinja
    └── content/  # By default, Ursus will use this content directory
        ├── posts/
        │   ├── hello-world.md
        │   ├── foo.md
        │   └── bar.md
        └── images/
            └── example.png
    ```
2. **Create a config file for your website.** You can copy `ursus/default_config.py`. If you call your config `ursus_config.py` and place it in your project root, it will be loaded automatically. Otherwise you must call ursus with the `-c` argument. If no config is set, Ursus will use the defaults set in `ursus/default_config.py`.
3. **Call the `ursus` command.**

### Running Ursus

Ursus comes with the `ursus` command. It accepts these arguments:

* `-w` or `--watch`: Reload the website when Content or Template files change.
* `-c` or `--config`: Run with the supplied configuration file. It accepts a Python file path `path/to/your_config.py`, or a Python module name `project.conf.ursus.py`. If not set, Ursus will look for `./ursus_config.py`.
* `-f` or `--fast`: Combined with `-w`, favours rebuild speed over completeness. It only rebuilds pages for the files that changed, not files that may refer to them.

#### Building from Sublime Text

You can configure Sublime Text to run Ursus when you press Cmd + B:

```json
// Sublime user settings or project config
{
    // ...
    "build_systems": [{
        "cmd": ["ursus", "-c", "$project_path/path/to/ursus_config.py"],
        "name": "Ursus",
    }],
    // ...
}

```