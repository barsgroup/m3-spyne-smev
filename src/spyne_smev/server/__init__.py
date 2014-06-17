# -*- coding: utf-

"""               
__init__.py.py
                  
:Created: 12 Jun 2014  
:Author: tim    
"""
from spyne.interface.wsdl.wsdl11 import Wsdl11


class _AllYourInterfaceDocuments(object):

    def __init__(self, interface):

        interface_document_type = getattr(
            interface.app.in_protocol,
            '_interface_document_type',
            Wsdl11)
        self.wsdl11 = interface_document_type(interface)
