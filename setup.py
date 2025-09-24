from setuptools import setup, find_packages
from pathlib import Path

root_dir = Path(__file__).parent

long_description = (root_dir / "README.md").read_text()
requirements_path = root_dir / "requirements.txt"
install_requires = requirements_path.read_text().strip().split('\n')

setup(
    name='ursus_ssg',
    version='1.4.2',
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
    install_requires=install_requires,
    zip_safe=False,
)
