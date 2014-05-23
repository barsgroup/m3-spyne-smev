# -*- coding: utf-8 -*-

"""
wsfactory_default_config.py

:Created: 5/15/14
:Author: timic
"""

import os
import shutil

from django.core.management import BaseCommand

import wsfactory


class Command(BaseCommand):

    args = "< path >"

    def handle(self, path, *args, **options):

        config_path = os.path.join(os.path.dirname(
            wsfactory.__file__), "schema", "config.xml")
        shutil.copy(config_path, path)
        print "OK!"


