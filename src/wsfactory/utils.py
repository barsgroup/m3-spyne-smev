# -*- coding: utf-8 -*-

"""
helpers.py

:Created: 4/4/14
:Author: timic
"""


from spyne.model.complex import ComplexModelMeta, ComplexModelBase


def namespace(ns):

    ComplexModel = ComplexModelMeta(
        "ComplexModel", (ComplexModelBase,), {"__namespace__": ns})

    return ComplexModel
