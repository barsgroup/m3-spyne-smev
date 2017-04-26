# -*- coding: utf-8 -*-

"""
application.py

:Created: 4/3/14
:Author: timic
"""
import logging
logger = logging.getLogger(__name__)

from six import binary_type

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
        except Fault as e:
            logger.exception(e)
            raise
        except Exception as e:
            e_text = format_exc()
            if isinstance(e_text, binary_type):
                e_text = e_text.decode("utf-8", errors="ignore")
            self.event_manager.fire_event("method_call_exception", e_text)
            logger.exception(e)
            raise InternalError(e)
