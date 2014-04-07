# -*- coding: utf-8 -*-

"""
app_meta.py

:Created: 3/12/14
:Author: timic
"""
import actions
from controller import controller


def register_actions():
    controller.packs.extend((
        actions.ApiPack(),
        actions.ServicePack(),
        actions.ServiceApiPack()
    ))


