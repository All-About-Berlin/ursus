from setuptools import setup, find_packages
from pathlib import Path
long_description = (Path(__file__).parent / "README.md").read_text()

setup(
    name='ursus_ssg',
    version='1.2.0',
    description='Static site generator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://github.com/all-about-berlin/ursus',
    author='Nicolas Bouliane',
    author_email='contact@nicolasbouliane.com',
    license='MIT',
    packages=find_packages(),
    scripts=['bin/ursus'],
    entry_points={
        'markdown.extensions': [
            'better_footnotes = ursus.context_processors.markdown:FootnotesExtension',
            'jinja = ursus.context_processors.markdown:JinjaExtension',
            'responsive_images = ursus.context_processors.markdown:ResponsiveImagesExtension',
            'superscript = ursus.context_processors.markdown:SuperscriptExtension',
            'tasklist = ursus.context_processors.markdown:TaskListExtension',
        ]
    },
    python_requires='>=3.11',
    install_requires=[
        'coloredlogs==15.0.1',
        'GitPython==3.1.30',
        'imagesize==1.4.1',
        'Jinja2==3.1.2',
        'jinja2-simple-tags==0.5.0',
        'libsass==0.22.0',
        'lunr==0.6.2',
        'Markdown==3.5.0',
        'MarkupSafe==2.1.1',
        'ordered-set==4.1.0',
        'PyMuPDF==1.21.1',
        'Pillow==9.4.0',  # Pillow-simd is much faster, but requires binaries to be installed separately.
        'watchdog==2.2.1',
        'requests==2.31.0',
        'rjsmin==1.2.1',
        'rcssmin==1.1.1',
    ],
    zip_safe=False,
)
