# coding: utf-8
import os
from os.path import dirname
from os.path import join

from setuptools import find_packages
from setuptools import setup
from setuptools.command.install import install


def _read(file_name):
    with open(join(dirname(__file__), file_name)) as f:
        return f.read()


class CustomInstallCommand(install):
    u"""Кастомизированная команда setuptools install.

    Параметр --no-binary=cryptography позволяет загружать пакет cryptography
    без пакета openssl. Без этого параметра в версиях cryptography 2.x
    автоматически загружается пакет openssl 1.1.x, в котором нет нужных нам гост
    алгоритмов. При использовании же параметра --no-binary=cryptography
    пакет cryptography будет использовать пакет openssl, установленный
    в системе.
    """
    @staticmethod
    def _add_pip_no_binary_values(values):
        u"""Добавляет значения в переменную окружения PIP_NO_BINARY.

        :param values: добавляемые значения (имена пакетов)
        :type values: list, tuple или str
        """
        assert type(values) in (list, tuple, str)
        new_values = [values] if isinstance(values, str) else values

        old_values = os.environ.get('PIP_NO_BINARY', '')
        if old_values.lower() == ':none:':
            raise ValueError("You can't change 'PIP_NO_BINARY', "
                             "because it's setted in :none:")
        if old_values.lower() == ':all:':
            return

        old_values = old_values.split(',') if old_values else []
        f_old_values = {str.lower(v) for v in old_values}
        f_new_values = {str.lower(v) for v in new_values}

        old_values.extend(f_new_values - f_old_values)
        os.environ['PIP_NO_BINARY'] = ','.join(old_values)

    def run(self):
        self._add_pip_no_binary_values('cryptography')
        install.run(self)


setup(
    cmdclass={
        'install': CustomInstallCommand,
    },
    name='m3-spyne-smev',
    url='https://stash.bars-open.ru/projects/M3/repos/spyne-smev/browse',
    license='MIT',
    author='BARS Group',
    author_email='bars@bars-open.ru',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    description=_read('DESCRIPTION'),
    long_description=_read('README.md'),
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Natural Language :: Russian',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django :: 1.4',
        'Framework :: Django :: 1.5',
        'Framework :: Django :: 1.6',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
    ],
    dependency_links=(
        'http://pypi.bars-open.ru/simple/m3-builder',
    ),
    setup_requires=(
        'm3-builder>=1.1',
    ),
    install_requires=(
        "lxml",
        "cryptography>=2.2.2,<3",
        "requests>=2,<3",
        "spyne>=2.11,<3",
        "suds>=0.4,<1; python_version == '2.7'",
        "suds-py3>=1.3.3.0,<2; python_version > '2.7'",
    ),
    set_build_info=dirname(__file__),
)
