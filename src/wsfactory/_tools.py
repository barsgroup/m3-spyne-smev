# -*- coding: utf-8 -*-

"""
factory.py

:Created: 3/13/14
:Author: timic
"""
import os
from threading import RLock
from functools import wraps
from importlib import import_module
from StringIO import StringIO
from lxml import etree

from spyne.application import Application
from spyne.service import ServiceBase


def load(path):
    mod, obj = path.rsplit('.', 1)
    mod = import_module(mod)
    return getattr(mod, obj)


def lock(fn):
    _lock = RLock()

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            _lock.acquire()
            result = fn(*args, **kwargs)
        finally:
            _lock.release()
        return result

    return wrapper


def load_xml(xml_path):
    """
    Загружает xml в etree.ElementTree
    """
    if os.path.exists(xml_path):
        xml_io = open(xml_path, 'rb')
    else:
        raise ValueError(xml_path)
    xml = etree.parse(xml_io)
    xml_io.close()
    return xml


def load_schema(schema_path):
    """
    Загружает схему xsd
    """
    if schema_path.startswith('http://') or schema_path.startswith('https://'):
        import requests
        response = requests.get(schema_path)
        schema_io = StringIO(response.text)
    elif os.path.exists(schema_path):
        schema_io = open(schema_path, 'rb')
    else:
        raise ValueError(schema_path)
    schema = etree.XMLSchema(file=schema_io)
    schema_io.close()
    return schema


def create_application(name, tns, service, in_protocol, out_protocol):
    from wsfactory._application import WSFactoryApplication
    from django.views.decorators.csrf import csrf_exempt

    app = Application(
        [service], tns,
        name=name,
        in_protocol=in_protocol,
        out_protocol=out_protocol)
    django_app = csrf_exempt(WSFactoryApplication(app))

    return django_app


def create_service(service_name, api_list):

    bases = (ServiceBase,)
    api_dict = dict(api_list)
    return type(str(service_name), bases, api_dict)


def create_protocol(protocol, security=None, **params):
    from wsfactory.smev.protocols import Soap11WSSE

    if not issubclass(protocol, Soap11WSSE) and security:
        raise ValueError(
            "Security can be applied only to Soap11WSSE subclasses")
    if security:
        params['wsse_security'] = security
    return protocol(**params)

el_name_with_ns = lambda ns: lambda el: '{%s}%s' % (ns, el)


class Cap(object):
    """
    Заглушка
    """

    def __getattr__(self, name):
        return self.__dict__.get(name, Cap())

    def __nonzero__(self):
        return False


def copy_with_nsmap(element, nsmap):
    """
    Создаёт копию элемента etree.Element с новым nsmap'ом.
    """
    new_nsmap = element.nsmap.copy()
    new_nsmap.update(nsmap)
    new_element = etree.Element(element.tag, nsmap=new_nsmap, **element.attrib)
    new_element.extend(element.getchildren())
    return new_element