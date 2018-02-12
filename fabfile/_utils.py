# coding: utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys


if sys.version_info.major == 2:
    from contextlib import nested
else:
    from fabric.context_managers import nested
