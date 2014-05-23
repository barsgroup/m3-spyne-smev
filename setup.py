import os
from distutils.core import setup


def read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as fd:
        return fd.read()

setup(
    name='wsfactory',
    version='0.1.0',
    packages=['wsfactory', 'wsfactory.smev', 'wsfactory.smev.smev256',
              'wsfactory.management', 'wsfactory.management.commands',
              'wsfactory.migrations'],
    package_dir={'': 'src'},
    package_data={'': ['schema/*', 'templates/ui-js/*']},
    url='http://bitbucket.org/timic/wsfactory',
    license=read_file("LICENSE"),
    description=read_file("DESCRIPTION"),
    author='Timur Salyakhutdinov',
    author_email='t.salyakhutdinov@gmail.com',
    requires=['lxml', 'spyne'],
)
