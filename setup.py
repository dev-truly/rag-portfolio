
import sys
from glob import glob
from os.path import splitext, basename

from setuptools import setup

__version__ = "2.1.3"

from setuptools.config.expand import find_packages

setup(
    name="personaai_default",
    version=__version__,
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.pyfiles')],
    install_requires=[
        'python-semantic-release==9.1.1',
        'pyfiglet==1.0.2',
        'python-dotenv==1.0.1'
    ],
)