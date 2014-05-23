# -*- coding: utf-8 -*-

"""
app_meta.py

:Created: 3/12/14
:Author: timic
"""

from django.conf.urls import url, patterns

import objectpack

from wsfactory.urls import urlpatterns
from wsfactory.views import track_config

import actions
from controller import controller


def register_actions():
    controller.packs.extend((
        actions.ServicePack(),
        actions.SecurityPack(),
        actions.ApiPack(),
        actions.ApplicationPack(),
        actions.LogPack(),
    ))


def register_desktop_menu():
    objectpack.uificate_the_controller(controller)


def register_urlpatterns():
    prefix, view = controller.urlpattern

    result = urlpatterns + patterns("", url(prefix, track_config(view)))
    return result
