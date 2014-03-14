# -*- coding: utf-8 -*-

"""
:Created: 3/12/14
:Author: timic
"""
from spyne.protocol.soap.soap11 import Soap11


class Soap11WSSE(Soap11):
    """
    Протокол SOAP с поддержкой

    :param wsse_security: Объек WS-Security
    :type wsse_security: wsfactory.smev.security.BaseWSSecurity

    >>> smev_params = {'sender_id': 5346212, 'sender_name': 'EPGU1214' }

    """

    def __init__(
        self, app=None, validator=None, xml_declaration=True,
        cleanup_namespaces=True, encoding='UTF-8', pretty_print=False,
        wsse_security=None,
    ):

        super(Soap11WSSE, self).__init__(
            app, validator, xml_declaration,
            cleanup_namespaces, encoding, pretty_print)
        self.wsse_security = wsse_security

    def create_in_document(self, ctx, charset=None):
        super(Soap11WSSE, self).create_in_document(ctx, charset)
        if self.wsse_security:
            in_document, _ = ctx.in_document
            self.wsse_security.validate(in_document)

    def create_out_string(self, ctx, charset=None):
        if self.wsse_security:
            ctx.out_document = self.wsse_security.apply(ctx.out_document)
        super(Soap11WSSE, self).create_out_string(ctx, charset)


class BaseSmev(Soap11WSSE):
    """
    Базовый класс для протоколов СМЭВ

    .. note::
        Конкретные реализации протоколов должны перегрузить методы
        :func:`decompose_smev_envelope` и :func:`construct_smev_envelope`

    :param smev_params: Словарь с параметрами для СМЭВ
    """
    def __init__(
            self, app=None, validator=None, xml_declaration=True,
            cleanup_namespaces=True, encoding='UTF-8', pretty_print=False,
            wsse_security=None, smev_params=None):
        super(BaseSmev, self).__init__(
            app, validator, xml_declaration,
            cleanup_namespaces, encoding,
            pretty_print, wsse_security)
        self.smev_params = smev_params or {}

    def deserialize(self, ctx, message):
        super(BaseSmev, self).deserialize(ctx, message)
        self.decompose_smev_envelope(ctx, message)

    def serialize(self, ctx, message):
        self.construct_smev_envelope(ctx, message)
        super(BaseSmev, self).serialize(ctx, message)

    def decompose_smev_envelope(self, ctx, message):
        raise NotImplementedError()

    def construct_smev_envelope(self, ctx, message):
        raise NotImplementedError()