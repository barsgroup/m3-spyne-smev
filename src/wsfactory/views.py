# -*- coding: utf-8 -*-

"""
views.py

:Created: 3/19/14
:Author: timic
"""

from django.http import HttpResponse, Http404

from wsfactory.settings import Settings


def api_list(request):
    """

    TODO: придумать как отдавать доку по сервисам
    """
    return HttpResponse()


def handle_api_call(request, Service, InProto, OutProto=None):
    OutProto = OutProto or InProto
    service_handler = Settings.get_app(Service, InProto, OutProto)
    if service_handler:
        return service_handler(request)
    else:
        raise Http404("Service not found")
