# -*- coding: utf-8 -*-

"""
xmlns.py

:Created: 3/13/14
:Author: timic
"""

smev245 = "http://smev.gosuslugi.ru/rev111111"
smev256 = "http://smev.gosuslugi.ru/rev120315"
inf = "http://smev.gosuslugi.ru/inf"
soapenv = soap = "http://schemas.xmlsoap.org/soap/envelope/"
ds = "http://www.w3.org/2000/09/xmldsig#"
wsse = (
    "http://docs.oasis-open.org/wss/2004/01/"
    "oasis-200401-wss-wssecurity-secext-1.0.xsd")
wsu = (
    "http://docs.oasis-open.org/wss/2004/01/"
    "oasis-200401-wss-wssecurity-utility-1.0.xsd")
v25 = "http://idecs.atc.ru/orderprocessing/ws/eventservice/v25/"
gostr3410 = "http://www.w3.org/2001/04/xmldsig-more#gostr34102001-gostr3411"
gostr3411hash = "http://www.w3.org/2001/04/xmldsig-more#gostr3411"
c14n = "http://www.w3.org/2001/10/xml-exc-c14n#"

_nsmap = {
    'wsse': wsse,
    'wsu': wsu,
    'inf': inf,
    'ds': ds,
}
nsmap256 = _nsmap.copy()
nsmap256.update({'soapenv': soapenv, 'smev': smev256})

nsmap245 = _nsmap.copy()
nsmap245.update({'soap': soap, 'smev': smev245})