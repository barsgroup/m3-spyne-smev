# -*- coding: utf-8 -*-

"""
helpers.py

:Created: 4/4/14
:Author: timic
"""


import mock

from spyne.model.complex import ComplexModelMeta, ComplexModelBase


def namespace(ns):

    ComplexModel = ComplexModelMeta(
        "ModelBase", (ComplexModelBase,), {"__namespace__": ns})

    return mock.patch('spyne.model.complex.ComplexModel', ComplexModel)
