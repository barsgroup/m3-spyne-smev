# -*- coding: utf-8 -*-

"""
actions.py

:Created: 3/12/14
:Author: timic
"""

from django.utils.translation import ugettext as _
from django.core.cache.backends.locmem import LocMemCache

from m3 import ApplicationLogicException
from m3.actions import ControllerCache

import objectpack

from wsfactory.ui.controller import observer
from wsfactory._helpers import get_cache
from wsfactory.config import Settings
from wsfactory.models import LogEntry
from wsfactory.ui import models
from wsfactory.ui import forms


class BaseWSPack(objectpack.ObjectPack):

    def declare_context(self, action):
        result = super(BaseWSPack, self).declare_context(action)
        if action in (
                self.save_action,
                self.new_window_action,
                self.edit_window_action):
            result[self.id_param_name] = {
                "type": lambda x: str(x) if (x and x != "0") else 0
            }
        elif action is self.delete_action:
            result[self.id_param_name] = {
                "type": lambda str_list: [
                    x.strip() for x in str_list.split(",")]
            }
        return result

    def extend_menu(self, menu):
        return menu_item(
            _(u"Администрирование"),
            _(u"Реестр веб-сервисов"),
            self.title,
            action=self.list_window_action,
            menu=menu)

    def save_row(self, obj, create_new, request, context):
        if obj.hash != Settings.hash():
            raise ApplicationLogicException(
                _(u"Версия конфигурации устарела!"))

        super(BaseWSPack, self).save_row(obj, create_new, request, context)


class ServicePack(BaseWSPack):

    model = models.Service

    add_window = edit_window = forms.ServiceEditWindow

    columns = [
        {
            "data_index": "code",
            "header": _(u"Код"),
        },
        {
            "data_index": "name",
            "header": _(u"Наименование"),
        }
    ]

    def __init__(self):
        super(ServicePack, self).__init__()
        self.select_api_action = ApiSelectAction()
        self.actions.append(self.select_api_action)

    def get_edit_window_params(self, params, request, context):
        params = super(ServicePack, self).get_edit_window_params(
            params, request, context)
        params["select_api_url"] = self.select_api_action.get_absolute_url()
        return params


class ApiPack(objectpack.ObjectPack):

    model = models.Api

    column_name_on_select = "name"
    columns = [
        {
            "data_index": "code",
            "header": _(u"Код"),
        },
        {
            "data_index": "name",
            "header": _(u"Наименование"),
        }
    ]

    def declare_context(self, action):
        result = super(ApiPack, self).declare_context(action)

        if action in (self.select_window_action, self.rows_action):
            result["exclude"] = {"type": lambda x: x.strip(",")}

        return result

    def get_rows_query(self, request, context):
        return super(ApiPack, self).get_rows_query(request, context).exclude(
            id__in=context.exclude)


class ApiSelectAction(objectpack.SelectorWindowAction):

    def configure_action(self, request, context):
        self.data_pack = ControllerCache.find_pack(ApiPack)


class SecurityPack(BaseWSPack):

    model = models.Security

    add_window = edit_window = forms.SecurityEditWindow

    columns = [
        {
            "data_index": "code",
            "header": _(u"Код"),
            "width": 1,
        },
        {
            "data_index": "name",
            "header": _(u"Наименование"),
            "width": 2,
        },
    ]


class ApplicationPack(BaseWSPack):

    model = models.Application

    width = 800
    height = 600

    add_window = edit_window = forms.ApplicationEditWindow

    columns = [
        {
            "data_index": "name",
            "header": _(u"Код"),
            "width": 3,
        },
        {
            "data_index": "display_service",
            "header": _(u"Услуга"),
            "width": 3,
        },
        {
            "data_index": "display_in_protocol",
            "header": _(u"Входящий протокол"),
            "width": 2,
        },
        {
            "data_index": "display_out_protocol",
            "header": _(u"Исходящий протокол"),
            "width": 2,
        },
    ]

    def get_edit_window_params(self, params, request, context):
        params = super(ApplicationPack, self).get_edit_window_params(
            params, request, context)
        params["services"] = tuple(models.Service.objects.values_list(
            "code", "name"))
        params["security"] = ((0, ""),) + tuple(
            models.Security.objects.values_list("code", "name"))
        params["in_protocols"] = tuple(models.Protocol.objects.filter(
            direction__in=("BOTH", "IN")).values_list("code", "name"))
        params["out_protocols"] = tuple(models.Protocol.objects.filter(
            direction__in=("BOTH", "OUT")).values_list("code", "name"))
        return params


class LogPack(objectpack.ObjectPack):

    model = LogEntry

    width = 800
    height = 600

    list_sort_order = ("-time",)

    columns = [
        {
            "data_index": "time",
            "header": _(u"Время"),
            "width": 2,
            "sortable": True,
        },
        {
            "data_index": "url",
            "header": _("URL"),
            "width": 2,
        },
        {
            "data_index": "service",
            "header": _(u"Услуга"),
            "width": 2,
            "searchable": True,
            "sortable": True,
        },
        {
            "data_index": "api",
            "header": _(u"Метод"),
            "width": 2,
        },
        {
            "data_index": "in_object",
            "header": _(u"Параметры запроса"),
            "width": 3,
        },
        {
            "data_index": "request",
            "header": _(u"Запрос"),
            "width": 1,
        },
        {
            "data_index": "response",
            "header": _(u"Ответ"),
            "width": 1,
        },
        {
            "data_index": "traceback",
            "header": _(u"Трассировка ошибки"),
            "width": 1,
        }
    ]

    def extend_menu(self, menu):
        return menu_item(
            _(u"Администрирование"),
            _(u"Реестр веб-сервисов"),
            self.title,
            action=self.list_window_action,
            menu=menu)


@observer.subscribe
class CheckCache(object):

    listen = [
        ".*/(ApplicationPack|ServicePack|SecurityPack)/"
        "Object(Save|AddWindow|EditWindow|Delete)Action"
    ]

    def before(self, request, context):
        cache = get_cache("wsfactory")
        if isinstance(cache, LocMemCache):
            raise ApplicationLogicException(
                _(u"Данная операция не поддерживается!"))


def menu_item(*path, **params):
    action = params.get("action")
    menu = params.get("menu")
    path = list(path)
    item = menu.Item(path.pop(), action)
    while path:
        item = menu.SubMenu(path.pop(), item)
    return item