# -*- coding: utf-8 -*-

"""
_xmlns.py

:Created: 3/13/14
:Author: timic
"""

smev245 = "http://smev.gosuslugi.ru/rev111111"
smev256 = "http://smev.gosuslugi.ru/rev120315"
inf = "http://smev.gosuslugi.ru/inf"
soapenv = "http://schemas.xmlsoap.org/soap/envelope/"
wsdl = "http://schemas.xmlsoap.org/wsdl/"
soap = "http://schemas.xmlsoap.org/wsdl/soap/"
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
xs = "http://www.w3.org/2001/XMLSchema"
base64enc = (
    "http://docs.oasis-open.org/wss/2004/01"
    "/oasis-200401-wss-soap-message-security-1.0#Base64Binary")
x509_token_profile = (
    "http://docs.oasis-open.org/wss/2004/01/"
    "oasis-200401-wss-x509-token-profile-1.0#X509v3")

nsmap = {
    'xs': xs,
    'soapenv': soapenv,
    'soap': soap,
    'wsse': wsse,
    'wsu': wsu,
    'inf': inf,
    'ds': ds,
    'wsdl': wsdl,
}
nsmap256 = nsmap.copy()
nsmap256.update({'smev': smev256})

nsmap245 = nsmap.copy()
nsmap245.update({'smev': smev245})