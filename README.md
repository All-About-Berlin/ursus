# Ursus

Ursus is the static site generator used by [All About Berlin](https://allaboutberlin.com) and my [personal website](https://nicolasbouliane.com). It turns Markdown files and [Jinja](https://jinja.palletsprojects.com/) templates into a static website.

It also renders images in different sizes, renders SCSS, minifies JS and generates Lunr.js search indexes.

This project is in active use and development.

## Setup

### Installation

Install Ursus with pip:

```bash
pip install ursus-ssg
```

### Getting started

Call `ursus` to generate a static website. Call `ursus --help` to see the command line options it supports.

By default, Ursus looks for 3 directories, relative to the current directory:

- It looks for content in `./content`
- It looks for page templates in `./templates`
- It generates a static website in `./output`

For example, create a markdown file and save it as `./content/posts/first-post.md`.

```markdown
---
title: Hello world!
description: This is an example page
date_created: 2022-10-10
---

## Hello beautiful world

*This* is a template. Pretty cool eh?
```

Then, create a page template and save it as `./templates/posts/entry.html.jinja`. 

```
<!DOCTYPE html>
<html>
<head>
    <title>{{ entry.title }}</title>
    <meta name="description" content="{{ entry.description }}">
</head>
<body>
    {{ entry.body }}

    Created on {{ entry.date_created }}
</body>
</html>
```

Your project should now look like this:

```
my-website/ <- You are here
├─ content/
│  └─ posts/
│     └─ first-post.md
└─ templates/
   └─ posts/
      └─ entry.html.jinja
```

Call `ursus` to generate a statuc website. It will create `./output/posts/first-post.html`.

### Configuring Ursus

To configure Ursus, create a configuration file.

```python
# Example Ursus config file
# Find all configuration options in `ursus/config.py`.
from ursus.config import config

config.content_path = Path(__file__).parent / 'blog'
config.templates_path = Path(__file__).parent / 'templates'
config.output_path = Path(__file__).parent.parent / 'dist'

config.site_url = 'https://allaboutberlin.com'

config.minify_js = True
config.minify_css = True
```

If you call your configuration file `ursus_config.py`, Ursus loads it automatically.

```
my-website/
├─ ursus_config.py
├─ content/
└─ templates/
```

You can also load a configuration file with the `-w` argument.

```bash
ursus -c /path/to/config.py
```

### Watching for changes

Ursus can rebuild your website when the content or templates change.

```bash
# Rebuild when content or templates change
ursus -w
ursus --watch
```

It can only rebuild the pages that changed. This is much faster, but it does not work perfectly.

```bash
# Only rebuild the pages that changed
ursus -wf
ursus --watch --fast
```

### Serving the website

Ursus can serve the website it generates. This is useful for testing.

```bash
# Serve the static website on port 80
ursus -s
ursus --serve 80
```

This is not meant for production. Use nginx, Caddy or some other static file server for that.

## How Ursus works

1. **Context processors** generate the context used to render templates. The context is just a big dictionary.
2. **Renderers** use the context and the templates to render the parts of the final website: pages, thumbnails, static assets, etc.

### Content

**Content** is what fills your website: text, images, videos, PDFs. Content is usually *rendered* to create a working website. Some content (like Markdown files) is rendered with Templates, and other (like images) is converted to a different file format.

Ursus looks for content in `./content`, unless you change `config.content_path`.

### Entries

A single piece of content is called an **Entry**. This can be a single image, a single markdown file, etc.

Each Entry has a **URI**. This is the Entry's unique identifier. The URI is the Entry's path relative to the content directory. For example, the URI of `./content/posts/first-post.md` is `posts/first-post.md`.

### Context

The **Context** contains the information needed to render your website. It's just a big dictionary, and you can put anything in it.

`context['entries']` contains is a dictionary of all your entries. The key is the Entry URI.

**Context processors** each add specific data to the context. For example, `MarkdownProcessor` adds your `.md` content to `context.entries`.

```python
# Example context
{
    'entries': {
        'posts/first-post.md': {
            'title': 'Hello world!',
            'description': 'This is an example page',
            'date_created': datetime(2022, 10, 10),
            'body': '<h2>Hello beautiful world</h2><p>...',
        },
        'posts/second-post.md': {
            # ...
        },
    },
    # Context processors can add more things to the context
    'blog_title': 'Example blog',
    'site_url': 'https://example.com/blog',
}
```

### Templates

**Templates** are used to render your Content. They are the theme of your website. Jinja templates, Javascript, CSS and theme images belong in the templates directory.

Ursus looks for templates in `./templates`, unless you change `config.templates_path`.

### Renderers

**Renderers** use the Context and the Templates to generate parts of your static website. For example, `JinjaRenderer` renders Jinja templates, `ImageTransformRenderer` converts and resizes your images, and `StaticAssetRenderer` copies your static assets.

### Output

This is the final static website generated by Ursus. Ursus generates a static website in `./output`, unless you change `config.output_path`.

The content of the output directory is ready to be served by any static file server.

## How context processors work

Context processors transform the context, which is a dict with information about each of your Entries.

Context processors ignore file and directory names that start with `.` or `_`. For example, `./content/_drafts/hello.md` and `./content/posts/_post-draft.md` are ignored.

### MarkdownProcessor

The `MarkdownProcessor` creates context for all `.md` files in `content_path`. The markdown content is in the `body` attribute.

```python
{
    'entries': {
        'posts/first-post.md': {
            'title': 'Hello world!',
            'description': 'This is an example page',
            'date_created': datetime(2022, 10, 10),
            'body': '<h2>Hello beautiful world</h2><p>...',
        },
        # ...
    },
}
```

It makes a few changes to the default markdown output:

- Put the front matter in the context
    - `related_*` keys are replaced by a list of related entry dicts
    - `date_` keys are converted to `datetime` objects
    - Other attributes are added to the entry object.
- Use responsive images based on `config.image_transforms` settings.
- `<img>` are converted to `<figure>` or `<picture>` tags when appropriate.
- Images are lazy-loaded with the `loading=lazy` attribute.
- Jinja tags (`{{ ... }}` and `{% ... %}`) are rendered as-is. You can use `{% include %}` and `{{ variables }}` in your content.

### GetEntriesProcessor

The `GetEntriesProcessor` adds a `get_entries` method to the context. It's used to get a list of entries of a certain type, and sort it.

```jinja
{% set posts = get_entries('posts', filter_by=filter_function, sort_by='date_created', reverse=True) %}

{% for post in posts %}
...
```

### GitDateProcessor

Adds the `date_updated` attribute to all Entries. It uses the file's last commit date.

```python
{
    'entries': {
        'posts/first-post.md': {
            'date_updated': datetime(2022, 10, 10),
            # ...
        },
        # ...
    },
}
```

### ImageProcessor

Adds images and PDFs Entries to the context. Dimensions and image transforms are added to each Entry. Use in combination with `config.image_transforms`.

```python
{
    'entries': {
        'images/hello.jpg': {
            'width': 320,
            'height': 240,
            'image_transforms': [
                {
                    'is_default': True,
                    'input_mimetype': 'image/jpeg',
                    'output_mimetype': 'image/webp',
                    # ...
                },
                # ...
            ]
        },
        # ...
    },
}
```

## How renderers work

Renderers use context and templates to generate parts of the static website.

A **Generator** takes your Content and your Templates and produces an Output. It's a recipe to turn your content into a final result. The default **StaticSiteGenerator** generates a static website. You can write your own Generator to output an eBook, a PDF, or anything else.

### ImageTransformRenderer

Renders images in your content directory.

- Images are converted and resized according to `config.image_transforms`.
- Files that can't be transformed (PDF to PDF) are copied as-is to the output directory.
- Images that can't be resized (SVG to anything) are copied as-is to the output directory.
- Image EXIF data is removed.

This renderer does nothing unless `config.image_transforms` is set:

```python
from ursus.config import config

config.image_transforms = {
    # ./content/images/test.jpg
    # ---> ./output/images/test.jpg
    # ./content/images/test.pdf
    # ---> ./output/images/test.pdf
    '': {
        'include': ('images/*', 'documents/*'),
        'output_types': ('original'),
    },
    # ./content/images/test.jpg
    # ---> ./output/images/content2x/test.jpg
    # ---> ./output/images/content2x/test.webp
    'content2x': {
        'include': ('images/*', 'illustrations/*'),
        'exclude': ('*.pdf', '*.svg'),
        'max_size': (800, 1200),
        'output_types': ('webp', 'original'),
    },
    # ./content/documents/test.pdf
    # ---> ./output/documents/pdfPreviews/test.png
    # ---> ./output/documents/pdfPreviews/test.webp
    'pdfPreviews': {
        'include': 'documents/*',
        'max_size': (300, 500),
        'output_types': ('webp', 'png'),
    },
}
```

### JinjaRenderer

Renders `*.jinja` files in the templates directory.

The output file has the same name and relative path as the template, but the `.jinja` extension is removed.

```
my-website/
├─ templates/
│  ├─ contact.html.jinja
│  ├─ sitemap.xml.jinja
│  └─ posts/
│     └─ index.html.jinja
└─ output/
   ├─ contact.html
   ├─ sitemap.xml
   └─ posts/
      └─ index.html
```

Files named `entry.*.jinja` will render every entry with the same relative path.

```
my-website/
├─ content/
│  └─ posts/
│     ├─ first-post.md
│     ├─ second-post.md
│     └─ _draft.md
├─ templates/
│  └─ posts/
│     └─ entry.html.jinja
└─ output/
   └─ posts/
      ├─ first-post.html
      └─ second-post.html
```

Files or directory names that start with `.` or `_` are not rendered.

```
my-website/
├─ content/
│  └─ posts/
│     ├─ hello-world.md
│     ├─ .hidden.md
│     └─ _drafts
│        └─ not-rendered.md
├─ templates/
│  └─ posts/
│     └─ entry.html.jinja
└─ output/
   └─ posts/
      └─ hello-world.html
```

### StaticAssetRenderer

Copies all files under `./templates` except `.jinja` files to the same subdirectory in `./output`. Files starting with `.` are ignored. Files and directories starting with `_` are ignored.

```
my-website/
├─ templates/
│  ├─ _ignored.jpg
│  ├─ styles.css
│  ├─ images/
│  │  └─ hello.png
│  └─ js/
│     └─ test.js
└─ output/
   ├─ styles.css
   ├─ images/
   │  └─ hello.png
   └─ js/
      └─ test.js
```

It uses hard links instead of copying files, so it does not use extra disk space.

## How generators work

Generators bring it all together. A generator takes all of your files, and generates some final product. There is only `StaticSiteGenerator`, which generates a static website. Custom generators could generate a book or a slideshow from the same content and templates.

## How linters work

Ursus supports linter. They verify the content when `ursus lint` is called. You can find examples in `ursus/linters`.