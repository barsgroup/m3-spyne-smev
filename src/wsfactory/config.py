# -*- coding: utf-8 -*-

"""
config.py

:Created: 5/12/14
:Author: timic
"""
import logging

logger = logging.getLogger(__name__)

import hashlib
import os
from lxml import etree, objectify


from wsfactory._helpers import (
    load_schema, load_xml, load, get_cache,
    create_service, create_protocol, create_application)

try:
    from wsfactory.smev import WSSecurity
except ImportError, ex:
    logger.error("Import Error: %s" % ex.message)
    WSSecurity = None


VALUE_TYPES = {
    "unicode": unicode,
    "int": int,
    "bool": lambda x: x in ("True", "true", True)
}


def parse_params(params):
    return dict((
        param.attrib["key"],
        VALUE_TYPES.get(param.attrib["valueType"])(param.text)
    ) for param in params)


class ImproperlyConfigured(Exception):
    pass


class Settings(object):

    __instance = None

    NAMESPACE = "http://bars-open.ru/schema/wsfactory"
    DEFAULT_TNS = "http://bars-open.ru/inf"
    CACHE_KEY = "wsfactory_config_file_hash"
    SCHEMA = load_schema(os.path.join(os.path.dirname(
        __file__), "schema", "wsfactory.xsd"))

    def __new__(cls, *more):
        if not cls.__instance:
            obj = cls.__instance = super(Settings, cls).__new__(cls, *more)

            obj._app_cache = {}
            obj._configured = False
            obj._config_path = None
            obj._hash = None
            obj._protocols = {}
            obj._api = {}
            obj._services = {}
            obj._security = {}
            obj._applications = {}
        return cls.__instance

    @classmethod
    def reload(cls):
        if not cls.configured():
            raise ImproperlyConfigured(
                "Not configured yet!")
        config_path = cls.config_path()
        cls.__instance = None
        cls.load(config_path)

    @classmethod
    def validate(cls, xml):
        schema = load_schema(os.path.join(os.path.dirname(
            __file__), "schema", "wsfactory.xsd"))
        if not schema.validate(etree.fromstring(etree.tostring(xml))):
            raise ImproperlyConfigured(
                "Config file didn't pass validation: %s\n"
                % "\n".join(err.message for err in schema.error_log))

    @classmethod
    def load(cls, config_path):
        logger.debug("Load configuration file %s" % config_path)
        cls.__instance = None
        config = cls()
        config._config_path = config_path

        # 1. Читаем настройки

        if not os.path.exists(config_path):
            raise ImproperlyConfigured(
                "Configuration file `%s` does not exist!"
                % config_path)

        xml = load_xml(config_path)
        cls.validate(xml)

        document = objectify.parse(config_path).getroot()

        # 2. Парсим протоколы

        element = document.Protocols.Protocol
        while not element is None:
            entry = dict(element.attrib.iteritems())
            entry["module_path"] = element.attrib["module"]
            entry["module"] = load(element.attrib["module"])
            entry["params"] = parse_params(element.getchildren())
            config._protocols[entry.pop("code")] = entry
            element = element.getnext()

        # 3. Парсим api

        element = document.ApiRegistry.Api
        while not element is None:
            entry = dict(element.attrib.iteritems())
            entry["module_path"] = element.attrib["module"]
            entry["module"] = load(element.attrib["module"])
            config._api[entry.pop("code")] = entry
            element = element.getnext()

        # 4. Парсим сервисы

        element = document.Services.Service
        while not element is None:
            api_code_set = set(
                el.attrib["code"] for el in element.getchildren())
            for api_code in api_code_set:
                if not api_code in config._api.iterkeys():
                    raise ImproperlyConfigured(
                        "Api with code `%s` does not found!" % api_code)
            config._services[element.attrib["code"]] = {
                "name": element.attrib["name"],
                "api": api_code_set}
            element = element.getnext()

        # 5. Парсим профиль безопасности

        element = getattr(
            document, "SecurityProfile", None
        ) and document.SecurityProfile.Security
        while not element is None:
            entry = dict(element.attrib.iteritems())
            config._security[entry.pop("code")] = entry
            element = element.getnext()

        # 6. Парсим приложения Spyne

        element = document.Applications.Application
        while not element is None:
            in_proto = element.InProtocol.attrib["code"]
            out_proto = element.OutProtocol.attrib["code"]
            if not all(map(
                    lambda code: code in config._protocols.iterkeys(),
                    (in_proto, out_proto))):
                raise ImproperlyConfigured(
                    "Protocol does not found!")
            entry = dict(element.attrib.iteritems())
            entry["in_protocol"] = dict(
                element.InProtocol.attrib.iteritems())
            entry["in_protocol"]["params"] = parse_params(
                element.InProtocol.getchildren())
            entry["out_protocol"] = dict(
                element.OutProtocol.attrib.iteritems())
            entry["out_protocol"]["params"] = parse_params(
                element.OutProtocol.getchildren())
            name = entry.pop("name", "-".join((
                entry["service"], in_proto, out_proto)))
            config._applications[name] = entry
            element = element.getnext()

        # 7. Посчитаем хеш-сумму файла конфигурации, и запишем её в кэш django
        with open(config_path, "rb") as fd:
            config._hash = hashlib.md5(fd.read()).hexdigest()

        cache = get_cache("wsfactory")
        cache.set(cls.CACHE_KEY, config._hash)
        config._configured = True

        logger.debug(
            "Configuration file %s successfully loaded" % config_path)

    @classmethod
    def to_xml(cls):
        if not cls.configured():
            raise ImproperlyConfigured(
                "Configuration does not loaded yet")

        config = cls()
        document = etree.Element("WSConfig", nsmap={None: cls.NAMESPACE})

        # 1. Дампим системные настройки
        params = filter(
            lambda (_key, _value): not _key.startswith("_"),
            config.__dict__.iteritems())
        elements = params and etree.SubElement(document, "System")
        for key, value in params:
            etree.SubElement(
                elements, "Param", key=key, valueType=type(value).__name__
            ).text = value

        # 2. Дампим протоколы

        elements = etree.SubElement(document, "Protocols")
        for key, value in config._protocols.iteritems():
            element = etree.SubElement(
                elements, "Protocol",
                code=key, name=value["name"], direction=value["direction"],
                module=value["module_path"])
            for param_key, param_value in value["params"].iteritems():
                etree.SubElement(
                    element, "Param", key=param_key,
                    valueType=type(param_value).__name__).text = param_value

        # 3. Дампим api

        elements = etree.SubElement(document, "ApiRegistry")
        for key, value in config._api.iteritems():
            etree.SubElement(
                elements, "Api", code=key, name=value["name"],
                module=value["module_path"])

        # 4. Дампим сервисы

        elements = etree.SubElement(document, "Services")
        for key, value in config._services.iteritems():
            element = etree.SubElement(
                elements, "Service", code=key, name=value["name"])
            for api_code in value["api"]:
                etree.SubElement(element, "Api", code=api_code)

        # 5. Дампим профиль безопасности

        elements = config._security and etree.SubElement(
            document, "SecurityProfile")
        for key, value in config._security.iteritems():
            element = etree.SubElement(
                elements, "Security", code=key, **value)

        # 6. Дампим приложения Spyne

        elements = etree.SubElement(document, "Applications")
        for key, value in config._applications.iteritems():
            element = etree.SubElement(
                elements, "Application", name=key, service=value["service"])
            if "tns" in value:
                element.attrib["tns"] = value["tns"]
            in_protocol = etree.SubElement(
                element, "InProtocol", code=value["in_protocol"]["code"])
            if "security" in value["in_protocol"]:
                in_protocol.attrib["security"] = value[
                    "in_protocol"]["security"]
            for param_key, param_value in value[
                    "in_protocol"]["params"].iteritems():
                etree.SubElement(
                    in_protocol, "Param", key=param_key,
                    valueType=type(param_value).__name__).text = unicode(
                        param_value)
            out_protocol = etree.SubElement(
                element, "OutProtocol", code=value["out_protocol"]["code"])
            if "security" in value["out_protocol"]:
                out_protocol.attrib["security"] = value[
                    "out_protocol"]["security"]
            for param_key, param_value in value[
                    "out_protocol"]["params"].iteritems():
                etree.SubElement(
                    out_protocol, "Param", key=param_key,
                    valueType=type(param_value).__name__).text = param_value

        return document

    @classmethod
    def dump(cls, config_path):

        document = cls.to_xml()
        cls.validate(document)

        logger.debug("Dump configutation file %s" % config_path)
        if not os.access(os.path.exists(
                config_path) and config_path or os.path.dirname(
                    config_path), os.W_OK):
            raise ImproperlyConfigured(
                "Permission denied `%s`" % config_path)
        # Записываем результат в файл
        with open(config_path, "w") as fd:
            fd.write(etree.tostring(
                document, pretty_print=True, encoding="utf8"))

        logger.debug(
            "Configuration file %s successfully dumped" % config_path)

    def _create_protocol(self, code, params, security=None):
        proto_params = self._protocols[code]["params"].copy()
        proto_params.update(params)
        security_params = (security and self._security[security] or {}).copy()
        security_params.pop("name", None)
        return create_protocol(
            self._protocols[code]["module"],
            WSSecurity and security and WSSecurity(**security_params),
            **proto_params)

    def _create_app(self, service_name):
        params = self._applications[service_name]
        api = map(
            lambda api_code: (api_code, self._api[api_code]["module"]),
            self._services[params["service"]]["api"],
        )
        service = create_service(params["service"], api)
        in_protocol = self._create_protocol(**params["in_protocol"])
        out_protocol = self._create_protocol(**params["out_protocol"])
        app = create_application(
            service_name, params.get("tns", self.DEFAULT_TNS),
            service, in_protocol, out_protocol)
        self._app_cache[service_name] = app
        return app

    @classmethod
    def get_service_handler(cls, service_name):
        self = cls()
        if not service_name in self._applications.iterkeys():
            return None
        return self._app_cache.setdefault(
            service_name, self._create_app(service_name))

    @classmethod
    def configured(cls):
        self = cls()
        return self._configured

    @classmethod
    def config_path(cls):
        return cls()._config_path

    @classmethod
    def hash(cls):
        self = cls()
        return self._hash

    @classmethod
    def get_registry(cls, registry):
        self = cls()
        result = {
            "api": self._api,
            "protocols": self._protocols,
            "applications": self._applications,
            "services": self._services,
            "security": self._security,
        }.get(registry, None)
        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    Settings.load(
        os.path.join(os.path.dirname(__file__), "schema", "config.xml"))

    conf1 = Settings()

    Settings.dump("/tmp/test.xml")
    Settings.load("/tmp/test.xml")

    conf2 = Settings()

    assert not conf1 is conf2
    assert conf1._protocols == conf2._protocols
    assert conf1._api == conf2._api
    assert conf1._services == conf2._services
    assert conf1._security == conf2._security
    assert conf1._applications == conf2._applications