# -*- coding: utf-8 -*-

"""
models.py

:Created: 3/19/14
:Author: timic
"""
import logging
logger = logging.getLogger(__name__)

import datetime
import os
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import ugettext as _

from wsfactory.config import Settings


def upload_handler(instance, filename):

    return os.path.join(
        settings.UPLOADS, "wsfactory",
        datetime.datetime.now().strftime("%Y/%m/%d"),
        "%s.log" % uuid.uuid4().hex)


class LogEntry(models.Model):
    """
    Лог запросов к сервисам
    """

    time = models.DateTimeField(
        verbose_name=_(u"Время выполнения запроса"),
        auto_now_add=True)
    url = models.CharField(max_length=100, verbose_name=_("URL"))
    application = models.CharField(max_length=50, verbose_name=_(u"Услуга"))
    api = models.CharField(max_length=50, verbose_name=_(u"API-метод"))
    in_object = models.TextField(
        verbose_name=_(u"Параметры запроса"),
        null=True)
    request_file = models.FileField(
        upload_to=upload_handler,
        verbose_name=_(u"Запрос"), null=True)
    response_file = models.FileField(
        upload_to=upload_handler,
        verbose_name=_(u"Ответ"), null=True)
    traceback_file = models.FileField(
        upload_to=upload_handler,
        verbose_name=_(u"Трассировка ошибки"), null=True)

    class Meta:
        db_table = "wsfactory_log"
        verbose_name = _(u"Лог запросов")
        verbose_name_plural = _(u"Логи запросов")

    @property
    def service(self):
        app = Settings.get_registry("applications").get(
            self.application, None)
        return app and app.get("service", None) or "Unknown"

    def _get_file_field_url(self, field=None):
        try:
            return _(
                u'<a href="%s" target="_blank">Скачать</a>'
                % getattr(self, "_".join((field, "file"))).url)
        except ValueError:
            return ""

    def _set_file_field(self, value, field=None):
        getattr(self, "_".join((field, "file"))).save(
            name=".".join((field, "log")), content=ContentFile(value))

    @property
    def request(self):
        return self._get_file_field_url("request")

    @request.setter
    def request(self, value):
        self._set_file_field(value, "request")

    @property
    def response(self):
        return self._get_file_field_url("response")

    @response.setter
    def response(self, value):
        self._set_file_field(value, "response")

    @property
    def traceback(self):
        return self._get_file_field_url("traceback")

    @traceback.setter
    def traceback(self, value):
        self._set_file_field(value, "traceback")