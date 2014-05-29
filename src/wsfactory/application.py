# -*- coding: utf-8 -*-

"""
application.py

:Created: 4/3/14
:Author: timic
"""
import logging
from spyne.model.complex import ComplexModelBase

logger = logging.getLogger(__name__)

from traceback import format_exc

from spyne.model.fault import Fault
from spyne.application import Application as SpyneApplication
from spyne.error import InternalError
from spyne.server.django import DjangoApplication
from spyne.interface.wsdl import Wsdl11


class ApiError(Fault):
    """
    Специальный exception, который может быть возбужден в api-методе.

    Специальным образом обрабатывается в потомках исходящего протокола
    Soap11WSSE: вместо Fault в body soap-конверта кладется вызываемый
    soap-message c элементом Error внутри.

    В остальных протоколах вёдет себя как обычный Fault

    TODO: пока необходимо явно передавать имя api-метода в котором возбуждается
    исключение
    """

    detail = None
    faultactor = "Server"

    def __init__(
            self, errorCode, errorMessage, messageName):
        self.errorCode = errorCode
        self.errorMessage = errorMessage
        self.messageName = messageName

    @property
    def faultcode(self):
        return self.errorCode

    @property
    def faultstring(self):
        return self.errorMessage

    def __repr__(self):
        return u"Error(%s: %s)" % (self.errorCode, self.errorMessage)


class Application(SpyneApplication):
    """
    Замена Application из spyne. Позволяет дополнительно обрабатывать эксепшны

    файрит ивент, method_call_exception, но в аргументе передает не контекст,
    а форматированный текст exception
    """

    def call_wrapper(self, ctx):
        try:
            return super(Application, self).call_wrapper(ctx)
        except Fault, e:
            logger.exception(e)
            raise
        except Exception, e:
            e_text = unicode(format_exc(), errors="ignore")
            self.event_manager.fire_event("method_call_exception", e_text)
            logger.exception(e)
            raise InternalError(e)


class _AllYourInterfaceDocuments(object):

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
        self.doc = _AllYourInterfaceDocuments(app.interface)