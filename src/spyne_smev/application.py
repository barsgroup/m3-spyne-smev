# coding: utf-8
from __future__ import absolute_import

from traceback import format_exc
import logging

from spyne.application import Application as SpyneApplication
from spyne.error import InternalError
from spyne.model.fault import Fault


logger = logging.getLogger(__name__)


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
