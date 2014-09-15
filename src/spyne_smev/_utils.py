# -*- coding: utf-8 -*-

"""
factory.py

:Created: 3/13/14
:Author: timic
"""
import os
from StringIO import StringIO

from lxml import etree
from six import binary_type, text_type, PY3
from spyne.model.complex import ComplexModelMeta, ComplexModelBase

el_name_with_ns = lambda ns: lambda el: '{%s}%s' % (ns, el)


class EmptyCtx(object):

    def __getattr__(self, name):
        return self.__dict__.get(name, EmptyCtx())

    def __nonzero__(self):
        return False


def copy_with_nsmap(element, nsmap):

    new_nsmap = element.nsmap.copy()
    new_nsmap.update(nsmap)
    new_element = etree.Element(element.tag, nsmap=new_nsmap, **element.attrib)
    new_element.extend(element.getchildren())

    return new_element


def namespace(ns):

    return ComplexModelMeta(
        "ComplexModel", (ComplexModelBase,), {"__namespace__": ns})


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


def native(s):
    """
    Convert :py:class:`bytes` or :py:class:`unicode` to the native
    :py:class:`str` type, using UTF-8 encoding if conversion is necessary.

    :raise UnicodeError: The input string is not UTF-8 decodeable.

    :raise TypeError: The input is neither :py:class:`bytes` nor
        :py:class:`unicode`.
    """
    if not isinstance(s, (binary_type, text_type)):
        raise TypeError("%r is neither bytes nor unicode" % s)
    if PY3:
        if isinstance(s, binary_type):
            return s.decode("utf-8")
    else:
        if isinstance(s, text_type):
            return s.encode("utf-8")
    return s

if PY3:
    def byte_string(s):
        return s.encode("charmap")
else:
    def byte_string(s):
        return s


isnone = lambda obj: obj is None
notisnone = lambda obj: not obj is None