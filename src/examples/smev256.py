# -*- coding: utf-8 -*-

"""               
soap11wsse.py
                  
:Created: 24 Jun 2014  
:Author: tim    
"""
from wsgiref.simple_server import make_server

from spyne.service import ServiceBase
from spyne.decorator import rpc
from spyne.model.primitive import Integer, Unicode
from spyne.model.complex import Iterable

from spyne_smev.application import Application
from spyne_smev.server.wsgi import WsgiApplication
from spyne_smev.wsse.protocols import X509TokenProfile
from spyne_smev.smev256 import Smev256

TEST_PRIVATE_KEY = """\
-----BEGIN PRIVATE KEY-----
MEUCAQAwHAYGKoUDAgITMBIGByqFAwICJAAGByqFAwICHgEEIgIgA5kTZ1It9Zot
cWUB3wVSE1b7NCmcs3hNk/rxkFOUOOI=
-----END PRIVATE KEY-----\
"""

TEST_X509_CERT = """\
-----BEGIN CERTIFICATE-----
MIIH3TCCB4qgAwIBAgIQAc5y+/u2ndAAAALJBlcAAjAKBgYqhQMCAgMFADCCAVwx
GDAWBgUqhQNkARINMTEwMjkwMTAwNTM4MjEaMBgGCCqFAwOBAwEBEgwwMDI5MDEy
MDQzMTcxCzAJBgNVBAYTAlJVMR8wHQYDVQQHDBbQkNGA0YXQsNC90LPQtdC70YzR
gdC6MSYwJAYDVQQIDB0yOSDQkNGA0YXQsNC90LPQtdC70YzRgdC60LDRjzEeMBwG
CSqGSIb3DQEJARYPdWNAZHZpbmFsYW5kLnJ1MTcwNQYDVQQKDC7Qk9CQ0KMg0JDQ
niAi0KPQv9GA0LDQstC70LXQvdC40LUg0JjQmtCiINCQ0J4iMXUwcwYDVQQDDGzQ
o9C00L7RgdGC0L7QstC10YDRj9GO0YnQuNC5INGG0LXQvdGC0YAg0J/RgNCw0LLQ
uNGC0LXQu9GM0YHRgtCy0LAg0JDRgNGF0LDQvdCz0LXQu9GM0YHQutC+0Lkg0L7Q
sdC70LDRgdGC0LgwHhcNMTMwNjI3MDYwMzAwWhcNMTQwNjI3MDYwMzAwWjCCAY8x
GDAWBgUqhQNkARINMTExODM4MzAwMDk3NzEaMBgGCCqFAwOBAwEBEgwwMDI5ODMw
MDgwNzgxIDAeBgkqhkiG9w0BCQEWEXphbUBpdC5hZG0tbmFvLnJ1MQswCQYDVQQG
EwJSVTEmMCQGA1UECAwdMjkg0JDRgNGF0LDQvdCz0LXQu9GM0YHQutCw0Y8xHDAa
BgNVBAcME9Cd0LDRgNGM0Y/QvS3QnNCw0YAxcDBuBgNVBAoMZ9Ca0L7QvNC40YLQ
tdGCINC/0L4g0LjQvdGE0L7RgNC80LDRgtC40LfQsNGG0LjQuCDQndC10L3QtdGG
0LrQvtCz0L4g0LDQstGC0L7QvdC+0LzQvdC+0LPQviDQvtC60YDRg9Cz0LAxcDBu
BgNVBAMMZ9Ca0L7QvNC40YLQtdGCINC/0L4g0LjQvdGE0L7RgNC80LDRgtC40LfQ
sNGG0LjQuCDQndC10L3QtdGG0LrQvtCz0L4g0LDQstGC0L7QvdC+0LzQvdC+0LPQ
viDQvtC60YDRg9Cz0LAwYzAcBgYqhQMCAhMwEgYHKoUDAgIkAAYHKoUDAgIeAQND
AARAfg6ZnBb19edoil9onjEiz0VZnWqZ9+wLoyTE6SWbBlPfdJagezjSZ+10dIla
5EImMFSf/CO9cWUY0VPadSBhsIEJADA2NTcwMDAyo4ID4DCCA9wwOAYDVR0lBDEw
LwYIKwYBBQUHAwIGCCsGAQUFBwMEBgYqhQNkAgIGByqFAwICIgYGCCqFAwUBGAIG
MCEGBSqFA2RvBBgMFtCa0YDQuNC/0YLQvtCf0YDQviBDU1AwgZMGBSqFA2RwBIGJ
MIGGDA7QlNC+0LzQtdC9LUtDMgwc0J/QkNCaINCj0KbQmtCjIFZpUE5ldCDQmtCh
Mgwt0KHQpC8xMTEtMTkyNCDQvtGCIDIwINCw0LLQs9GD0YHRgtCwIDIwMTIg0LMu
DCfQodCkLzEyMS0xODcxINC+0YIgMjYg0LjRjtC90Y8gMjAxMiDQsy4wewYIKwYB
BQUHAQEEbzBtMDQGCCsGAQUFBzAChihodHRwOi8vdWMuZHZpbmFsYW5kLnJ1L3Jv
b3Qvcm9vdDIwMTMuY2VyMDUGCCsGAQUFBzAChilodHRwOi8vdWMyLmR2aW5hbGFu
ZC5ydS9yb290L3Jvb3QyMDEzLmNlcjBwBgNVHR8EaTBnMDGgL6AthitodHRwOi8v
dWMuZHZpbmFsYW5kLnJ1L2NkcC8wNjU3X3JlbTIwMTMuY3JsMDKgMKAuhixodHRw
Oi8vdWMyLmR2aW5hbGFuZC5ydS9jZHAvMDY1N19yZW0yMDEzLmNybDCCAZ0GA1Ud
IwSCAZQwggGQgBTsme+5BarYbq7DcQyQgarqr17FOqGCAWSkggFgMIIBXDEYMBYG
BSqFA2QBEg0xMTAyOTAxMDA1MzgyMRowGAYIKoUDA4EDAQESDDAwMjkwMTIwNDMx
NzELMAkGA1UEBhMCUlUxHzAdBgNVBAcMFtCQ0YDRhdCw0L3Qs9C10LvRjNGB0Lox
JjAkBgNVBAgMHTI5INCQ0YDRhdCw0L3Qs9C10LvRjNGB0LrQsNGPMR4wHAYJKoZI
hvcNAQkBFg91Y0BkdmluYWxhbmQucnUxNzA1BgNVBAoMLtCT0JDQoyDQkNCeICLQ
o9C/0YDQsNCy0LvQtdC90LjQtSDQmNCa0KIg0JDQniIxdTBzBgNVBAMMbNCj0LTQ
vtGB0YLQvtCy0LXRgNGP0Y7RidC40Lkg0YbQtdC90YLRgCDQn9GA0LDQstC40YLQ
tdC70YzRgdGC0LLQsCDQkNGA0YXQsNC90LPQtdC70YzRgdC60L7QuSDQvtCx0LvQ
sNGB0YLQuIIQAc4Y1cTt6fAAAAHgBlcAAjAdBgNVHSAEFjAUMAgGBiqFA2RxATAI
BgYqhQNkcQIwCwYDVR0PBAQDAgTwMAwGA1UdEwEB/wQCMAAwHQYDVR0OBBYEFDXY
ynkiWma1JDt7ZIY+vWCYlekSMAoGBiqFAwICAwUAA0EAsdzqpgJXGNnQpPuqytUp
Cf5RD+YOsNHWu24Rk+LzSpoRg8UL+yD1617keO5jKeLe0Tr6lfONOB3HfmF8+HWv
Bw==
-----END CERTIFICATE-----\
"""

security = X509TokenProfile(
    private_key=TEST_PRIVATE_KEY, private_key_pass="12345678",
    certificate=TEST_X509_CERT)


class HelloService(ServiceBase):

    @rpc(Unicode, Integer, _returns=Iterable(Unicode))
    def SayHello(ctx, Name, Times):
        return (u"Hello, {0}!".format(Name) for _ in xrange(Times))

application = Application(
    [HelloService], "http://example.com/hello-world-tns", "HelloWorld",
    in_protocol=Smev256(wsse_security=security),
    out_protocol=Smev256(wsse_security=security))

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    wsgi_application = WsgiApplication(application)
    server = make_server("localhost", 8080, wsgi_application)
    server.serve_forever()


### client code
#
# from spyne_smev.client import Client
#
# client = Client(
#     "http://localhost:8080?wsdl",
#     private_key=TEST_PRIVATE_KEY, private_key_pass="12345678",
#     certificate=TEST_X509_CERT)
# msg = client.factory.create("SayHello")
# msg.Message.Sender.Code = "Sndr12345"
# msg.Message.Sender.Name = "Sender"
# msg.Message.Recipient.Code = "Rcpnt1234"
# msg.Message.Recipient.Name = "Recipient"
# msg.MessageData.AppData.Name = "John Smith"
# msg.MessageData.AppData.Times = 5
# greetings = client.service.SayHello(
#     msg.Message, msg.MessageData)
# if not client.last_verified:
#     raise ValueError(
#         "msg didn't pass validation checks. See debug log for details!")
# print "\n".join("{0}. {1}".format(i, name) for i, name in enumerate(
#     greetings.MessageData.AppData.string))
###