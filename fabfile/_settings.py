# coding: utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from os.path import abspath
from os.path import dirname
from os.path import join


#: Имя пакета с проектом.
PROJECT_PACKAGE = 'spyne_smev'


#: Папка проекта.
PROJECT_DIR = dirname(dirname(abspath(__file__)))


#: Папка с исходными кодами.
SRC_DIR = join(PROJECT_DIR, 'src')
