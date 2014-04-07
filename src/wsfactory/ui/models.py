# -*- coding: utf-8 -*-

"""
models.py

:Created: 3/19/14
:Author: timic
"""

from objectpack import VirtualModel


class Protocol(VirtualModel):
    """
    Прикладной протокол передачи данных бизнем логики. JSON, SOAP etc.
    """

    @classmethod
    def _get_ids(cls):
        pass

    def __init__(self):
        pass


class Api(VirtualModel):
    """
    Сервисное api или сервис-методы
    """

    @classmethod
    def _get_ids(cls):
        pass

    def __init__(self):
        pass


class Service(VirtualModel):
    """
    Услуги (они же сервисы)
    """


class ServiceApi(VirtualModel):
    """
    Service <---> Api
    """


class ServiceProtocol(VirtualModel):
    """
    Service <---> Protocol
    """


class LogEntry(models.Model):
    """
    Лог запросов к сервисам
    """

    IN = 1
    OUT = 2
    DIRECTIONS = (
        (IN, u'Входящий'),
        (OUT, u'Исходящий')
    )

    date = models.DateTimeField(
        verbose_name=u'Время выполнения запроса',
        default=datetime.now)
    direction = models.PositiveSmallIntegerField(
        choices=DIRECTIONS,
        default=IN,
        verbose_name=u'Направление запроса')
    service = models.CharField(max_length=50, verbose_name=u'Услуга')
    api = models.CharField(max_length=50, verbose_name=u'API-метод')
    in_protocol = models.CharField(
        max_length=50, verbose_name=u'Входящий протокол')
    out_protocol = models.CharField(
        max_length=50, verbose_name=u'Выходной протокол')
    request = models.TextField(verbose_name=u'Запрос', null=True)
    response = models.TextField(verbose_name=u'Ответ', null=True)
    traceback = models.TextField(verbose_name=u'Трассировка ошибки', null=True)

    class Meta:
        verbose_name = u'Лог запросов'
        verbose_name_plural = u'Логи запросов'
