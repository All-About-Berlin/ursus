from setuptools import setup, find_packages
from pathlib import Path
long_description = (Path(__file__).parent / "README.md").read_text()

setup(
    name='ursus_ssg',
    version='1.4.1',
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
    package_data={
        'ursus.babel': ['*', ],
        'ursus': ['py.typed', ],
    },
    python_requires='>=3.11',
    install_requires=[
        'babel==2.16.0',
        'GitPython==3.1.43',
        'imagesize==1.4.1',
        'Jinja2==3.1.4',
        'jinja2-simple-tags==0.6.1',
        'libsass==0.23.0',
        'lunr==0.7.0',
        'Markdown==3.5.2',
        'MarkupSafe==2.1.5',
        'ordered-set==4.1.0',
        'platformdirs==4.3.6',
        'PyMuPDF==1.24.5',
        'Pillow==10.3.0',
        'watchdog==4.0.1',
        'requests==2.32.3',
        'rjsmin==1.2.2',
        'rcssmin==1.1.2',
    ],
    zip_safe=False,
)
