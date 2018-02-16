# coding: utf-8
from __future__ import absolute_import

from spyne.interface.wsdl.wsdl11 import Wsdl11


class _AllYourInterfaceDocuments(object):

    def __init__(self, interface):

        interface_document_type = getattr(
            interface.app.in_protocol,
            '_interface_document_type',
            Wsdl11)
        self.wsdl11 = interface_document_type(interface)
