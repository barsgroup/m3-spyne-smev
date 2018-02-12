# coding: utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from os.path import join
import sys

from fabric.context_managers import cd
from fabric.decorators import task
from fabric.operations import local
from fabric.tasks import execute

from . import dist
from . import req
from . import src
from ._settings import PROJECT_DIR


@task
def clean():
    """Полная очистка от рабочих файлов."""
    execute(dist.clean)
    execute(src.clean)

    with cd(PROJECT_DIR):
        for path in ('.eggs', 'dist'):
            path = join(PROJECT_DIR, path)
            local('rm -f -r -d "{}"'.format(path))

        local('git gc --quiet')

        local('rm -f -r -d "{}"'.format('.tox'))
        local('rm -f .coverage')
