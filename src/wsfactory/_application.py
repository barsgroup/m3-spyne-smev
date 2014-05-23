# -*- coding: utf-8 -*-

"""
applicatiob.py

:Created: 4/3/14
:Author: timic
"""
from spyne.server.django import DjangoApplication
from spyne.interface.wsdl import Wsdl11


class AllYourInterfaceDocuments(object):

    def __init__(self, interface):

        interface_document_type = getattr(
            interface.app.in_protocol,
            '_interface_document_type',
            Wsdl11)
        self.wsdl11 = interface_document_type(interface)


class WSFactoryApplication(DjangoApplication):

    def __init__(self, app, chunked=True, max_content_length=2 * 1024 * 1024,
                 block_length=8 * 1024):
        super(WSFactoryApplication, self).__init__(
            app, chunked, max_content_length, block_length)
        self.doc = AllYourInterfaceDocuments(app.interface)