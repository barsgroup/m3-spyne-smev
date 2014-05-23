# -*- coding: utf-8 -*-

"""
helpers.py

:Created: 5/13/14
:Author: timic
"""
from lxml import etree

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