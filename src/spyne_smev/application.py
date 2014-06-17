# -*- coding: utf-8 -*-

"""
application.py

:Created: 4/3/14
:Author: timic
"""
import logging
logger = logging.getLogger(__name__)

from traceback import format_exc

from spyne.model.fault import Fault
from spyne.application import Application as SpyneApplication
from spyne.error import InternalError


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


