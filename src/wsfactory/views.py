# -*- coding: utf-8 -*-

"""
views.py

:Created: 3/19/14
:Author: timic
"""

import logging
logger = logging.getLogger(__name__)

from functools import wraps, partial
import traceback

from django.http import Http404
from django.views.decorators.csrf import csrf_exempt

from spyne import EventManager

from wsfactory.config import Settings
from wsfactory._helpers import get_cache
from wsfactory.models import LogEntry


def track_config(fn):

    @wraps(fn)
    def inner(*args, **kwargs):
        if not Settings.configured():
            from django.conf import settings
            config_path = getattr(settings, "WSFACTORY_CONFIG_FILE")
            logger.info(
                "Not configured yet. Load configuration %s" % config_path)
            Settings.load(config_path)
        cache = get_cache("wsfactory")
        if Settings.hash() != cache.get(Settings.CACHE_KEY):
            logger.info("Configuration file was changed. Reloading ...")
            Settings.reload()

        return fn(*args, **kwargs)

    return inner


@track_config
def api_list(request):
    """

    TODO: придумать как отдавать доку по сервисам
    """
    raise Http404("Not implemented yet")


def handle_wsgi_close(ctx, log=None):
    log.api = ctx.method_name
    log.in_object = unicode(ctx.in_object or "") or None


@track_config
def handle_api_call(request, service):
    service_handler = Settings.get_service_handler(service)
    if service_handler:

        logger.debug("Hitting service %s." % service)
        log = LogEntry(
            url="%s %s" % (request.method, request.get_full_path()),
            application=service)
        if request.body:
            log.request = request.body
        service_handler.event_manager.add_listener(
            "wsgi_close", partial(handle_wsgi_close, log=log))

        try:
            response = csrf_exempt(service_handler)(request)
        except Exception:
            log.traceback = unicode(traceback.format_exc(), errors="ignore")
            raise
        else:
            if response.content:
                log.response = response.content
        finally:
            log.save()
            service_handler.event_manager = EventManager(service_handler)

        return response
    else:
        msg = "Service %s not found" % service
        logger.info(msg)
        raise Http404(msg)

