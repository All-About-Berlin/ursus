from setuptools import setup, find_packages

setup(
    name='ursus',
    version='0.1',
    description='Static site generator',
    url='http://github.com/nicbou/ursus',
    author='Nicolas Bouliane',
    author_email='contact@nicolasbouliane.com',
    license='MIT',
    packages=find_packages(),
    scripts=['bin/ursus'],
    python_requires='>=3.10',
    install_requires=[
        'coloredlogs==15.0.1',
        'GitPython==3.1.30',
        'Jinja2==3.1.2',
        'lunr==0.6.2',
        'Markdown==3.4.1',
        'MarkupSafe==2.1.1',
        'ordered-set==4.1.0',
        'PyMuPDF==1.21.1',
        'Pillow==9.4.0',  # Pillow-simd is much faster, but requires binaries to be installed separately.
        'watchdog==2.2.1',
        'rjsmin==1.2.1',
        'rcssmin==1.1.1',
    ],
    zip_safe=False,
)
