# Ursus

Static site generator used by [All About Berlin](https://allaboutberlin.com). It turns Markdown files and Jinja templates into a static website.

This README is incomplete, as befits a project under active development.

## Features

- Customisable and extensible. It's not just for blogs.
- Relationships between objects. For example, related content.

## Basic concepts

### Content and Entries

**Content** is what fills your website: text, images, videos. A single piece of content is called an **Entry**. The location of the Content is set by the `content_path` config parameter. By default, it's under `./content`. You can have a different `content_path` for each Generator.

Content is usually *rendered* to create a working website. Some content is rendered with Templates.

For example:

- A markdown file that is rendered into an HTML page using a Template.
- An image that is served in different sizes
- A PDF file for which thumbnails are created

### Templates

**Templates** are used to render your Content. The same templates can be applied to different Entries, or even reused for a different website. That's why they are kept separate from your content.

The location of the Templates is set by the `templates_path` config parameter. By default, it's under `./templates`. You can have a different `templates_path` for each Generator.

For example:

- HTML templates that wrap a nice theme around your Content.
- Images and other static assets that are part of the website's theme

### Output

This is the final product created by Ursus. By default, the Output is a static website. You can configure Ursus to produce different types of Outputs in different locations.

The location of the Output is set by the `output_path` config parameter. By default, it's under `./output`. You can have a different `output_path` for each Generator.

## How Ursus works

### Generators

A **Generator** takes your Content and your Templates and produces an Output. The default **StaticSiteGenerator** generates a static website. You can write your own Generator to output an eBook, a PDF, or anything else. You can have multiple Generators if you need to produce multiple Outputs.

#### StaticSiteGenerator

Generates a static website.

### Context processors

A **ContextProcessor** turns your Content into an object that the Renderer uses to render Templates.

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

The `MarkdownProcessor` would generate a context object that looks like this:

```
{
    # Information about this entry
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

    # A list of all entries
    'entries': {
        'posts/hello-world.md': {...},
        'posts/foo.md': {...},
        'posts/bar.md': {...},
        'images/example.png': {...},
    }

    # This variable comes from the "globals" section of your config. It's an
    # example. You can set your own.
    'twitter_profile_url': 'https://twitter.com/aboutberlin',
}
```

Then, a Renderer can use this information to render a template into a fully working HTML page.

`FileContextProcessor`s create or transform the context for an individual Entry. For example, the `MarkdownProcessor` above.

`ContextProcessor`s transform the global context after all Entries are processed. For example, it can add a `related_content` field to your blog posts.

#### MarkdownProcessor

The `MarkdownProcessor` creates context for `.md` files.

#### IndexProcessor

The `IndexProcessor` creates an index of entries. For example, `context['entries']['posts']` returns a subset of `context['entries']` with only Entries that start with `posts/`: `posts/hello-world.md`, `posts/foo.md`, `posts/bar.md`, etc.

### Renderers

**Renderer**s put your Content into Templates, and render them into the desired Outputs.

#### ImageRenderer

Renders images in `content_path` with a few changes:

- Images are compressed and optimized.
- Images are resized according to the `output_image_sizes`. The images are shrunk if needed, but never stretched.
- The original image is hard linked in the output directory.
- Images that can't be resized (like SVG) are hard linked in the output directory.
- Image EXIF data is removed.

This renderer does nothing unless `output_image_sizes` is set:
```python
config = {
    # ...
    'generators': [
        (
            'ursus.generators.static.StaticSiteGenerator', {
                'renderers': [
                    # ...
                    'ursus.renderers.image.ImageRenderer',
                    # ...
                ],
                'output_image_sizes': {
                    # 'Transform name': (max width, max height),

                    # An empty name generates images in the same <output_path> directory.
                    # This image size is used by default.
                    # <content_path>/images/img.jpg -> <output_path>/images/img.jpg
                    '': (1600, 2400),

                    # A name generates images in a subdirectory
                    # <content_path>/images/img.jpg -> <output_path>/images/content2x/img.jpg
                    'original': (4000, 4000),
                    'content1x': (800, 1200),
                },
                # ...
            }
        )
    ],
    # ...
}
```

#### JinjaRenderer

Renders Jinja templates, fills them with your Content.

Files named `_entry.*.jinja` are rendered once for each Entry with the same path. For example, `<templates_path>/posts/_entry.html.jinja` will render `<content_path>/posts/hello-world.md`, `<content_path>/posts/foo.md` and `<content_path>/posts/bar.md`. The output path is the entry name with the extension replaced. If `<templates_path>/posts/_entry.html.jinja` renders `<templates_path>/posts/hello-world.md`, the output file is `<output_path>/posts/hello-world.html`.

All template files with the `.jinja` extension will be rendered. For example, `<templates_path>/posts/index.html.jinja` will be rendered as `<output_path>/posts/index.html`. Files starting with `_` are ignored.

The output path is the template name without the `.jinja` extension. For example, `index.html.jinja` will be rendered as `index.html`.

#### StaticAssetRenderer

Simply copies static assets (CSS, JS, images, etc.) under `templates_path` to the same subdirectory in `output_path`. Files starting with `.` are ignored. Files and directories starting with `_` are ignored.

## Getting started

1. Create a directory for your templates, and another for your content.
    ```
    example_site/
    ├── templates/
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
    │       └── _entry.html.jinja
    └── content/
        ├── posts/
        │   ├── hello-world.md
        │   ├── foo.md
        │   └── bar.md
        └── images/
            └── example.png
    ```
2. Create a config file for your website. Copy `config.py` for an example.
3. Call the `ursus` command.

### Running Ursus

Ursus comes with the `ursus` command. It accepts these arguments:

* `-w` or `--watch`: Reload the website when Content or Template files change.
* `-c` or `--config`: Run with the supplied configuration file. It accepts a Python file path `path/to/ursus_config.py`, or a Python module name `project.conf.ursus.py`

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