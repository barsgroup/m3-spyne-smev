# -*- coding: utf-8 -*-

"""
api.py

:Created: 3/12/14
:Author: timic
"""
from protocol_base import BaseSmev


class Smev244(BaseSmev):
    """
    Имплементация протокола СМЕВ версии 2.4.4
    """
    #TODO


class Smev245(BaseSmev):
    """
    Имплементация протокола СМЕВ версии 2.4.5
    """
    #TODO


class Smev255(BaseSmev):
    """
    Имплементация протокола СМЕВ версии 2.5.5
    """


class Smev256(BaseSmev):
    """
    Имплементация протокола СМЕВ версии 2.5.6
    """

    def decompose_smev_envelope(self, ctx, message):
        pass

    def construct_smev_envelope(self, ctx, message):
        pass