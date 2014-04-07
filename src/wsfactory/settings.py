# -*- coding: utf-8 -*-

"""
config.py

:Created: 3/26/14
:Author: timic
"""
import os
from logging import getLogger, DEBUG, ERROR, Filter, info
from logging.handlers import TimedRotatingFileHandler
from lxml import objectify

from wsfactory._tools import (
    load, load_schema, load_xml, lock, create_service, create_application,
    create_protocol)


DEFAULT_TNS = "http://bars-open.ru/inf"


class ImproperlyConfigured(Exception):
    pass


class LevelFilter(Filter):

    def __init__(self, name='', level=ERROR):
        super(LevelFilter, self).__init__(name)
        self.level = level

    def filter(self, record):
        result = super(LevelFilter, self).filter(record)
        return result and (record.levelno == self.level)


class NoLevelFilter(Filter):

    def __init__(self, name='', level=ERROR):
        super(NoLevelFilter, self).__init__(name)
        self.level = level

    def filter(self, record):
        result = super(NoLevelFilter, self).filter(record)
        return result and (record.levelno != self.level)


class Cache(object):

    __cache = {}

    def get(self, key):
        return self.__cache.get(key, None)

    @lock
    def add(self, key, value):
        self.__cache[key] = value


class Settings(object):

    __settings = None

    def __new__(cls, *more):
        if not cls.__settings:
            obj = cls.__settings = super(Settings, cls).__new__(
                cls, *more)
            obj.logger = getLogger("WSFactory")
            obj.logger.setLevel(ERROR)
            obj._config_path = None
            obj._config_schema = None
            obj._config_xml = None
            obj._ui_enabled = False
            obj._ui_permission_checkers = False
            obj._protocol_registry = {}
            obj._service_registry = {}
            obj._api_registry = {}
            obj._security_profile_registry = {}
            obj._service_protocol_registry = {}
            obj._service_cache = Cache()
            obj._app_cache = Cache()
        return cls.__settings

    def _configure_logger(self, level, log_dir):
        self.logger = getLogger("WSFactory")
        self.logger.setLevel(level)
        debug_handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, 'wsfactory_debug.log'), when='D')
        debug_handler.addFilter(LevelFilter("WSFactory", DEBUG))
        self.logger.addHandler(debug_handler)
        handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, 'wsfactory.log'), when='D')
        handler.addFilter(NoLevelFilter("WSFactory", DEBUG))
        self.logger.addHandler(handler)

    @classmethod
    def reset(cls):
        cls.__settings = None

    @classmethod
    def reload(cls):
        config_path = cls()._config_path
        if not config_path:
            raise ImproperlyConfigured("WSFactory: Not configured yet!")
        cls.load(config_path)

    @classmethod
    def load(cls, config_path):

        cls.reset()
        settings = cls()
        settings._config_path = config_path

        info("WSFactory: Load configuration ...")

        if not os.path.exists(config_path):
            raise ImproperlyConfigured(
                "WSFactory: File `%s` doesn't exists" % config_path)

        schema = load_schema(os.path.join(os.path.dirname(
            __file__), 'schema', 'wsfactory.xsd'))
        xml = load_xml(config_path)
        if not schema.validate(xml):
            raise ImproperlyConfigured(
                "WSFactory: Config file didn't pass validation checks: %s\n"
                % '\n'.join(err.message for err in schema.error_log))

        config = objectify.parse(config_path).getroot()
        settings._config_schema = schema
        settings._config_xml = config
        info("WSFactory: OK. Reading configuration ...")

        # настройки логов
        info("WSFactory: Initialize application logger ...")
        log_level = config.System.Logger.LogLevel.text
        log_dir = config.System.Logger.LogDir.text
        if not log_dir:
            log_dir = os.path.join(
                os.path.dirname(config_path), 'logs')
        if not os.path.isabs(log_dir):
            log_dir = os.path.join(
                os.path.dirname(config_path), log_dir)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        settings._configure_logger(log_level, log_dir)

        logger = settings.logger
        logger.info("Logger initialized!")

        # грузим протоколы
        logger.info("Loading protocols ...")
        protocol = config.WS.ProtocolRegistry.Protocol
        while protocol:
            try:
                proto_cls = load(protocol.Module.text)
            except (ImportError, AttributeError):
                logger.error(
                    "Import Error. Cannot load protocol `%s`" % protocol.Module.text)
                protocol = protocol.getnext()
                continue

            params = {}
            if hasattr(protocol, "Params"):
                for param in protocol.Params.getchildren():
                    _, param_name = param.tag.split("{%s}" % param.nsmap[None])
                    params[param_name] = param.text

            settings._protocol_registry[protocol.attrib['code']] = {
                "module": proto_cls,
                "direction": protocol.Direction.text,
                "name": protocol.Name.text,
                "doc": protocol.Doc.text,
                "params": params,
            }

            protocol = protocol.getnext()
        logger.info("Protocols were loaded")

        # грузим апи
        logger.info("Loading api ...")
        api = config.WS.ApiRegistry.Api
        while api:
            try:
                api_fn = load(api.Module.text)
            except (ImportError, AttributeError):
                logger.error(
                    "Import Error. Cannot load api `%s`" % api.Module)
                api = api.getnext()
                continue

            settings._api_registry[api.attrib['code']] = {
                'module': api_fn,
                'doc': api.Doc.text,
            }
            api = api.getnext()
        logger.info("Api methods were loaded")

        # грузим сервисы
        logger.info("Loading services ...")
        tns = config.WS.ServiceRegistry.attrib[
            'tns'] if 'tns' in config.WS.ServiceRegistry.attrib else DEFAULT_TNS
        service = config.WS.ServiceRegistry.Service
        while service:
            api_set = set()
            api = service.Api
            while not api is None:
                if not api.attrib['code'] in settings._api_registry:
                    logger.warning(
                        "Cannot find api `%s` for service `%s`"
                        % (api.attrib['code'], service.attrib['code']))
                else:
                    api_set.add(api.attrib['code'])
                api = api.getnext()
            if not api_set:
                logger.error(
                    "Improperly configured. No api defined for service `%s`"
                    % service.attrib['code'])
            else:
                settings._service_registry[service.attrib['code']] = {
                    'name': service.Name.text,
                    'doc': service.Doc.text,
                    'api': api_set,
                    'tns': service.attrib['tns']
                    if 'tns' in service.attrib else tns
                }

            service = service.getnext()
        logger.info("Services were loaded")

        # грузим профили-безопасности
        logger.info("Loading security profiles ...")
        security = config.WS.SecurityProfile.Security
        while security:
            try:
                security_cls = load(security.Module.text)
            except (ImportError, AttributeError):
                logger.error(
                    "Import Error. Cannot load security profile `%s`"
                    % security.Module.text)
                security = security.getnext()
                continue

            params = {}
            for param in security.Params.getchildren():
                _, param_name = param.tag.split("{%s}" % param.nsmap[None])
                params[param_name] = param.text

            settings._security_profile_registry[security.attrib['code']] = {
                "module": security_cls,
                "params": params,
            }
            security = security.getnext()
        logger.info("Security profiles were loaded")

        # грузим сервис-протоколы
        logger.info("Load service protocols ...")
        service = config.WS.ServiceProtocols.Service
        while service:
            registry = settings._service_protocol_registry.setdefault(
                service.attrib['code'], set())

            registry.add((
                service.inProtocol.attrib['code'],
                service.inProtocol.attrib['security']
                if 'security' in service.inProtocol.attrib else None,
                service.outProtocol.attrib['code'],
                service.outProtocol.attrib['security']
                if 'security' in service.outProtocol.attrib else None,
            ))
            service = service.getnext()
        logger.info("Service protocols were loaded")

        logger.info("Configuration was successfully loaded")

    @classmethod
    def get_app(cls, service, in_protocol, out_protocol):
        settings = cls()
        settings.logger.info("Getting service `%s`" % service)

        service_params = settings._service_registry.get(service, None)
        if not service_params:
            settings.logger.warning("Service `%s` not found!" % service)
            return

        service_protocols = settings._service_protocol_registry.get(
            service, None)
        if not service_protocols:
            settings.logger.warning(
                "Cannot find protocols for service `%s`" % service)
            return

        proto_found = False
        for protocols in service_protocols:
            in_proto, in_sec, out_proto, out_sec = protocols
            if (in_proto == in_protocol) and (out_proto == out_protocol):
                proto_found = True
                break
        if not proto_found:
            settings.logger.warning(
                "`%s/%s` in/out protocols for service `%s` doesn't defined"
                % (in_protocol, out_protocol, service))
            return

        app = settings._app_cache.get(
            (service, in_protocol, out_protocol))
        if app:
            return app
        return settings._create_application(
            service, in_proto, in_sec, out_proto, out_sec)

    def _create_application(
            self, service_name, in_proto_name, in_sec_name,
            out_proto_name, out_sec_name):

        self.logger.info(
            "Creating app instance for service `%s`\n"
            "in_protocol = %s, out_protocol = %s" % (
                service_name, in_proto_name, out_proto_name))

        service_instance = self._service_cache.get('service')
        service_params = self._service_registry.get(service_name, None)

        if not service_instance:
            self.logger.info("Creating service instance `%s`" % service_name)
            apis = (
                (code, api['module'])
                for code, api in self._api_registry.iteritems()
                if code in service_params['api'])

            service_instance = create_service(service_name, apis)
            self._service_cache.add(service_name, service_instance)

        in_proto_inst = self._create_protocol(
            in_proto_name, service_name, in_sec_name)
        out_proto_inst = self._create_protocol(
            out_proto_name, service_name, out_sec_name)

        app_name = '-'.join((service_name, in_proto_name, out_proto_name))
        app = create_application(
            app_name, service_params['tns'], service_instance,
            in_proto_inst, out_proto_inst)
        self._app_cache.add((service_name, in_proto_name, out_proto_name), app)
        return app

    def _create_protocol(self, proto_code, service_code, security_code=None):
        cls = self._protocol_registry[proto_code]['module']
        sec_inst = self._create_security(security_code) if security_code else None
        params = self._protocol_registry[proto_code]['params'].copy()

        proto_inst = create_protocol(cls, sec_inst, **params)
        return proto_inst

    def _create_security(self, security_code):
        cls = self._security_profile_registry[security_code]['module']
        inst = cls(**self._security_profile_registry[security_code]['params'])
        return inst

    @classmethod
    def getLogger(cls):
        return cls().logger

if __name__ == "__main__":

    test_conf_path = os.path.join(
        os.path.dirname(__file__), 'schema', 'config.xml')
    Settings.load(test_conf_path)
    test_settings = Settings()
    test_app = Settings.get_app('Declaration', 'soap11', 'soap11wsse')
    print test_app