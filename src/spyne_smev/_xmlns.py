# coding: utf-8
from __future__ import absolute_import


smev245 = "http://smev.gosuslugi.ru/rev111111"
smev255 = "http://smev.gosuslugi.ru/rev120315"
smev256 = "http://smev.gosuslugi.ru/rev120315"
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


sha1 = "http://www.w3.org/2000/09/xmldsig#sha1"
sha256 = "http://www.w3.org/2000/09/xmldsig#sha256"
sha512 = "http://www.w3.org/2000/09/xmldsig#sha512"
rsa_sha1 = "http://www.w3.org/2000/09/xmldsig#rsa-sha1"
rsa_sha256 = "http://www.w3.org/2000/09/xmldsig#rsa-sha256"
rsa_sha512 = "http://www.w3.org/2000/09/xmldsig#rsa-sha512"
md5 = "http://www.w3.org/2000/09/xmldsig-more#md5"
rsa_md5 = "http://www.w3.org/2000/09/xmldsig-more#rsa-md5"
gost94 = "http://www.w3.org/2001/04/xmldsig-more#gostr3411"
gost2001 = "http://www.w3.org/2001/04/xmldsig-more#gostr34102001-gostr3411"
gost2012_256 = (
    "urn:ietf:params:xml:ns:cpxmlsec:"
    "algorithms:gostr34102012-gostr34112012-256"
)
md_gost2012_256 = (
    "urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34112012-256"
)
gost2012_512 = (
     "urn:ietf:params:xml:ns:cpxmlsec:"
     "algorithms:gostr34102012-gostr34112012-512"
)
md_gost2012_512 = (
    "urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34112012-512"
)

exc_c14n = "http://www.w3.org/2001/10/xml-exc-c14n#"
exc_c14n_wc = "http://www.w3.org/2001/10/xml-exc-c14n#WithComments"
xml_c14n = "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
xml_c14n_wc = "http://www.w3.org/TR/2001/REC-xml-c14n-20010315#WithComments"

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
    'ds': ds,
    'wsdl': wsdl,
}
nsmap255 = nsmap.copy()
nsmap255.update({'smev': smev255})

nsmap256 = nsmap.copy()
nsmap256.update({'smev': smev256})

nsmap245 = nsmap.copy()
nsmap245.update({'smev': smev245})
