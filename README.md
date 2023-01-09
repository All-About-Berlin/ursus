# Ursus

Static site generator used by [All About Berlin](https://allaboutberlin.com). It turns Markdown files and Jinja templates into a static website.

## Features

- Customisable and extensible. It's not just for blogs.
- Relationships between objects. For example, related content.

## Basic concepts

### Content and Entries

**Content** is what fills your website: text, images, videos. A single piece of content is called an **Entry**.

Content is usually *rendered* to create a working website. Some content is rendered with Templates.

For example:

- A markdown file that is rendered into an HTML page using a Template.
- An image that is served in different sizes
- A PDF file for which thumbnails are created

### Templates

**Templates** are used to render your Content. The same templates can be applied to different Entries, or even reused for a different website. That's why they are kept separate from your content.

For example:

- HTML templates that wrap a nice theme around your Content.
- Images and other assets that are part of the website's theme


## How Ursus works

### The Generator

A **Generator** takes your Content and your Templates, and turns them into a website. The default **StaticSiteGenerator** generates static websites, but you can write a custom Generator to turn your Content into an eBook, a PDF, or anything other sort of output.

### Context processors

Context processors take your content, and create a Context that the Renderers can use.

For example, take this Entry, `posts/hello-world.md`:

```markdown
Title: Hello world!
Description: This is an example page
Date_created: 2022-10-10
Date_updated: 2023-01-01
Related_posts: posts/foo.md, posts/bar.md

## Hello beautiful world

*This* is a template
```

The final Context for this Entry would look like this:

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

    # You set these variables in your config. They can contain anything you want.
    'globals': {
        'site_url': 'https://example.com/',
        'custom_variable': 'foobar',
    },
}
```

This is what the Renderer would see when it renders the final HTML page for this Entry.

The Context has a lot more information than the original Entry:

- Metadata starting with `date_` is turned into datetime objects.
- Metadata starting with `related_` is turned into lists of Entry objects.
- A `url` key is added.
- An `entries` field is added, with a reference to all Entries.

The Context is created and transformed by `FileContextProcessor`s and `ContextProcessor`s. You can write your own.

### Renderers

**Renderer**s render the files that form your website. They render an Entry and its Context into files that appear on your website.

For example:

* The **JinjaRenderer** renders markdown Entries and Jinja templates into HTML files.


## Getting started

1. Create a directory for your templates, and another for your content.
    ```
    example_site/
    ├── templates/
    │   ├── index.html
    │   ├── css/
    │   │   └──style.css
    │   ├── js/
    │   │   └──scripts.js
    │   ├── fonts/
    │   │   ├── open-sans.svg
    │   │   ├── open-sans.ttf
    │   │   └── open-sans.woff
    │   └── posts/
    │       ├── index.html
    │       └── _entry.html
    └── content/
        ├── posts/
        │   ├── hello-world.md
        │   ├── foo.md
        │   └── bar.md
        └── images/
            └── example.png
    ```
2. Create a config file for your website. See `config.py` for an example.
3. Call `ursus` with your config file.