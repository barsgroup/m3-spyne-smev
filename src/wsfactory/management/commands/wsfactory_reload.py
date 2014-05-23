# -*- coding: utf-8 -*-

"""
wsfactory_reload.py

:Created: 5/15/14
:Author: timic
"""

from django.core.management import BaseCommand
from django.conf import settings

from wsfactory.config import Settings


class Command(BaseCommand):

    def handle(self, *args, **options):

        path = getattr(settings, "WSFACTORY_CONFIG_FILE", None)
        if not path:
            print "Config file path does not provided"
        else:
            print "Reloading configuration file %s ..." % path
            Settings.load(path)
            print "OK!"
