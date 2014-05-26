# -*- coding: utf-8 -*-

"""
applicatiob.py

:Created: 4/3/14
:Author: timic
"""
from traceback import format_exc

from spyne.application import Application as SpyneApplication
from spyne.server.django import DjangoApplication
from spyne.interface.wsdl import Wsdl11


class Application(SpyneApplication):
    """
    Замена Application из spyne. Позволяет дополнительно обрабатывать эксепшны

    файрит ивент, method_call_exception, но в аргументе передает не контекст,
    а форматированный текст exception
    """

    def call_wrapper(self, ctx):
        try:
            return super(Application, self).call_wrapper(ctx)
        except Exception, e:
            e_text = unicode(format_exc(), errors="ignore")
            self.event_manager.fire_event("method_call_exception", e_text)
            raise


class AllYourInterfaceDocuments(object):

    def __init__(self, interface):

        interface_document_type = getattr(
            interface.app.in_protocol,
            '_interface_document_type',
            Wsdl11)
        self.wsdl11 = interface_document_type(interface)


class WSFactoryApplication(DjangoApplication):

    def __init__(self, app, chunked=True, max_content_length=2 * 1024 * 1024,
                 block_length=8 * 1024):
        super(WSFactoryApplication, self).__init__(
            app, chunked, max_content_length, block_length)
        self.doc = AllYourInterfaceDocuments(app.interface)