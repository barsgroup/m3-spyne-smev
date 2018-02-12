# coding: utf-8
# pylint: disable=relative-import
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys

from fabric.api import local
from fabric.decorators import task


@task
def clean():
    """Удаление всех пакетов из окружения."""
    local(
        "pip freeze | "
        "egrep -v '\''pkg-resources'\'' | "
        "xargs pip uninstall -y"
    )
    local('pip install -U --force-reinstall setuptools pip')
    local(
        'pip install -U {}'.format(
            'fabric' if sys.version_info.major == 2 else 'fabric3'
        )
    )


@task
def dev():
    """Обновление списка зависимостей для development-среды."""
    packages = (
        'tox',
        'fabric' if sys.version_info.major == 2 else 'fabric3',
        'six',
        'isort',
        'pycodestyle',
        'pylint',
        'ipython',
        'ipdb',
        'pudb',
    )
    local('pip install -U ' + ' '.join(packages))
