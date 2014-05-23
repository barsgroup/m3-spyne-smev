# -*- coding: utf-8 -*-
"""
models.py

:Created: 5/23/14
:Author: timic
"""
import logging
logger = logging.getLogger(__name__)

import os

from django.utils.translation import ugettext as _
from django.utils import simplejson as json

from objectpack import VirtualModel, ValidationError

from wsfactory.config import Settings, VALUE_TYPES
from wsfactory._helpers import lock


class BaseWSVirtualModel(VirtualModel):

    _id_field = "code"
    _registry = None

    def __init__(self, init_data=None):
        init_data = init_data or {}
        self.__dict__.update(init_data)


class EditableWSModelMixin(object):

    def __init__(self, init_data=None):
        init_data = init_data or self.new()
        self.__dict__.update(init_data)

    @classmethod
    def new(cls):
        raise NotImplementedError()

    def to_registry(self):
        raise NotImplementedError()

    @lock
    def save(self):
        registry = Settings.get_registry(self._registry)
        id_key = getattr(self, self._id_field)

        if self.id != id_key and id_key in registry:
            raise ValidationError(_(
                u"%s с кодом %s уже существует!" % (
                    self._meta.verbose_name, id_key)
            ))
        registry[id_key] = self.to_registry()

        # если ключ изменился надо удалить старый
        if self.id != id_key:
            registry.pop(self.id, None)

        try:
            Settings.dump(Settings.config_path())
        finally:
            Settings.reload()

    @lock
    def safe_delete(self):
        id_key = getattr(self, self._id_field)
        registry = getattr(Settings(), "_%s" % self._registry)
        result = id_key in registry
        registry.pop(id_key)
        try:
            Settings.dump(Settings.config_path())
        finally:
            Settings.reload()
        return result


class Protocol(BaseWSVirtualModel):
    """
    Прикладной протокол передачи данных бизнем логики. JSON, SOAP etc.
    """

    _registry = "protocols"

    @classmethod
    def _get_ids(cls):
        protocols = Settings.get_registry(cls._registry)
        for key, value in protocols.iteritems():
            yield {
                "id": key,
                "code": key,
                "name": value["name"],
                "direction": value["direction"],
                "module": value["module_path"],
            }

    def display_direction(self):
        return {
            "BOTH": _(u'Вх./Исх.'),
            "IN": _(u'Входящий'),
            "OUT": _(u'Исходящий'),
        }.get(self.direction)


class Api(BaseWSVirtualModel):
    """
    Сервисное api или сервис-методы
    """

    _registry = "api"

    class _meta:
        verbose_name = _(u"Метод")
        verbose_name_plural = _(u"Методы")

    @classmethod
    def _get_ids(cls):
        api = Settings.get_registry(cls._registry)
        for key, value in api.iteritems():
            yield {
                "id": key,
                "code": key,
                "name": value["name"],
                "module": value["module_path"],
            }


class Service(EditableWSModelMixin, BaseWSVirtualModel):
    """
    Услуги (они же сервисы)
    """

    _registry = "services"

    class _meta:
        verbose_name = _(u"Услуга")
        verbose_name_plural = _(u"Услуги")

    @classmethod
    def _get_ids(cls):
        services = Settings.get_registry(cls._registry)
        config_hash = Settings.hash()
        for key, value in services.iteritems():
            yield {
                "hash": config_hash,
                "id": key,
                "code": key,
                "name": value["name"],
                "api": value["api"],
            }

    def save(self):
        if not self.api:
            raise ValidationError(_(u"Необходимо добавить методы в услугу!"))
        super(Service, self).save()

    def to_registry(self):
        return {
            "api": self.api,
            "name": self.name,
        }

    @classmethod
    def new(cls):
        return {
            "hash": Settings.hash(),
            "id": None,
            "code": None,
            "name": None,
            "api": set(),
        }

    @property
    def api_json(self):
        return json.dumps(list(self.api))

    @api_json.setter
    def api_json(self, value):
        self.api = set(json.loads(value))

    @property
    def api_data(self):
        api = Settings.get_registry("api")
        return tuple((code, code, api[code]["name"]) for code in self.api)


class Security(EditableWSModelMixin, BaseWSVirtualModel):

    _registry = "security"

    class _meta:
        verbose_name = _(u"Профиль безопасности WS-Security")
        verbose_name_plural = _(u"Профили безопасности WS-Security")

    @classmethod
    def _get_ids(cls):
        security = Settings.get_registry(cls._registry)
        for key, value in security.iteritems():
            item = {
                "hash": Settings.hash(),
                "id": key,
                "code": key,
            }
            item.update(value)
            yield item

    def to_registry(self):
        return {
            "name": self.name,
            "pem_file_name": self.pem_file_name,
            "private_key_pass": self.private_key_pass,
        }

    @classmethod
    def new(cls):
        return {
            "hash": Settings.hash(),
            "id": None,
            "code": None,
            "name": None,
            "pem_file_name": None,
            "private_key_pass": None,
        }

    def save(self):
        if not os.path.exists(self.pem_file_name):
            raise ValidationError(
                _(u"Файл подписи `%s` не найден!") % self.pem_file_name)
        super(Security, self).save()


class Application(EditableWSModelMixin, BaseWSVirtualModel):
    """
    Service <---> Protocol
    """

    _id_field = "name"
    _registry = "applications"

    class _meta:
        verbose_name = _(u"Веб-сервис")
        verbose_name_plural = _(u"Веб-сервисы")

    @classmethod
    def _get_ids(cls):
        apps = Settings.get_registry(cls._registry)
        config_hash = Settings.hash()
        for key, value in apps.iteritems():
            yield {
                "hash": config_hash,
                "id": key,
                "name": key,
                "service": value["service"],
                "tns": value.get("tns", None),
                "in_protocol": value["in_protocol"]["code"],
                "out_protocol": value["out_protocol"]["code"],
                "in_security": value["in_protocol"].get("security", None),
                "out_security": value["out_protocol"].get("security", None),
                "in_protocol_params": value["in_protocol"]["params"],
                "out_protocol_params": value["out_protocol"]["params"],
            }

    @classmethod
    def new(cls):

        return {
            "hash": Settings.hash(),
            "id": None,
            "name": None,
            "service": None,
            "tns": None,
            "in_security": None,
            "out_security": None,
            "in_protocol": None,
            "in_protocol_params": {},
            "out_protocol": None,
            "out_protocol_params": {},
        }

    def display_service(self):
        services = Settings.get_registry("services")
        return services[self.service]["name"]

    def display_in_protocol(self):
        protocols = Settings.get_registry("protocols")
        return protocols[self.in_protocol]["name"]

    def display_out_protocol(self):
        protocols = Settings.get_registry("protocols")
        return protocols[self.out_protocol]["name"]

    @property
    def in_protocol_params_json(self):
        return json.dumps([
            {
                "key": key,
                "value": value,
                "value_type": type(value).__name__
            } for key, value in self.in_protocol_params.iteritems()
        ])

    @property
    def out_protocol_params_json(self):
        return json.dumps([
            {
                "key": key,
                "value": value,
                "value_type": type(value).__name__
            } for key, value in self.out_protocol_params.iteritems()
        ])

    @property
    def in_protocol_params_data(self):
        return [
            (key, key, value, type(value).__name__)
            for key, value in self.in_protocol_params.iteritems()]

    @property
    def out_protocol_params_data(self):
        return [
            (key, key, value, type(value).__name__)
            for key, value in self.out_protocol_params.iteritems()]

    @in_protocol_params_json.setter
    def in_protocol_params_json(self, value):
        array = json.loads(value)
        self.in_protocol_params = dict(
            (item["key"], VALUE_TYPES[item["value_type"]](item["value"]))
            for item in array)

    @out_protocol_params_json.setter
    def out_protocol_params_json(self, value):
        array = json.loads(value)
        self.out_protocol_params = dict(
            (item["key"], VALUE_TYPES[item["value_type"]](item["value"]))
            for item in array)

    def to_registry(self):
        result = {
            "in_protocol": {
                "code": self.in_protocol,
                "params": self.in_protocol_params,
            },
            "out_protocol": {
                "code": self.out_protocol,
                "params": self.out_protocol_params,
            },
            "service": self.service,
        }
        if self.in_security:
            result["in_protocol"]["security"] = self.in_security
        if self.out_security:
            result["out_protocol"]["security"] = self.out_security
        return result