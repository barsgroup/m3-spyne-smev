# -*- coding: utf-8 -*-

"""               
soap11wsse.py
                  
:Created: 24 Jun 2014  
:Author: tim    
"""
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("spyne.protocol.xml").setLevel(logging.DEBUG)

from wsgiref.simple_server import make_server

from spyne.application import Application
from spyne.service import ServiceBase
from spyne.decorator import rpc
from spyne.server.wsgi import WsgiApplication
from spyne.model.primitive import Integer, Unicode
from spyne.model.complex import Iterable

from spyne_smev.wsse.protocols import Soap11WSSE, X509TokenProfile


TEST_PRIVATE_KEY = """\
-----BEGIN ENCRYPTED PRIVATE KEY-----
MIICxjBABgkqhkiG9w0BBQ0wMzAbBgkqhkiG9w0BBQwwDgQILapyqmvV6asCAggA
MBQGCCqGSIb3DQMHBAihoCXn4PchlwSCAoAYCMM3+EBICbcF92lHmqPha3jdcQbX
GT7h4LZrLDysm4ldG2eeArTO9Vci1FMmPHQtSjXhkTxsjIwscxOHDGDNiPIbbCjB
eoRpWisKGeW+H8HQWFCGZ5R9roKwIuAeqDbu3ZkK5MEDNWp6RMdwkMCz/n2MN8GA
pU4AMxPz+RCN9QNtJFJ2RIxLpL8xXmRil+86sK/0ivaUKEbRxB0jAvhv53GSQZDx
wasRwio90RpLhgSQwckGUSyMdQ4l7qjg7/RMpOUsVtaQpntc10KCi444OiKba6sA
4h0/4L+PvWLpAFFODeAFfXm4PngX8o1iuPrnKJJy0qxH+SdcULDr1gwhM4b0wZBS
ERdskuzh16iE/MgXcaPcik3iSEqClaCWsf1/AhsPldyJH3ab2jIdL7IALPQ34j3Z
e5MxlJ8fydSG7PNjVADZOpOw7oejW2RrajijeXkB3yZZInbpu1XJBNwvUjz6BpQM
Yl6MIkdplZjOWISncn1kaRdsMffjovamPRL3iMy07vaN2fKgw6PJo8A/qCLOxP3y
NzujSDDLrGv5QO2BxYfqv15Ii+joopyIeNft41q4W6ZdUrooUausgkyEQLhBpDZu
lobpGLn9Cy/IgGzqLcHWBwI3lRO8yyf7oipTumyUm4OmaXPB9vBlqw6ca2Xk0QxX
z2ztW1H1qqu+td98jFXEIoKiWJZLb7mScS6YIXFVlV1m+dqrZQoXnpRJmb9Xu/px
gBcqTUriF3+i0I29a/4y7ox0kcpk37D36F9vCtLqno9imbrTAXZvfz/Q05ChRL2d
tjQUHTEGz/nlWAhboDuehVvdVOLuNLovkZE64Ad9hlFW45KUAxZeqfQ9
-----END ENCRYPTED PRIVATE KEY-----\
"""

TEST_X509_CERT = """\
-----BEGIN CERTIFICATE-----
MIICvzCCAigCCQC/7ohvksUD1TANBgkqhkiG9w0BAQsFADCBozELMAkGA1UEBhMC
UlUxEjAQBgNVBAgMCVRBVEFSU1RBTjEOMAwGA1UEBwwFS0FaQU4xEzARBgNVBAoM
CkJBUlMgR3JvdXAxFzAVBgNVBAsMDkJBUlMtRWR1Y2F0aW9uMRUwEwYDVQQDDAxi
YXJzLW9wZW4ucnUxKzApBgkqhkiG9w0BCQEWHHRyc2FseWFodXRkaW5vdkBiYXJz
LW9wZW4ucnUwHhcNMTQwNjMwMDcwNzEzWhcNMTUwNjMwMDcwNzEzWjCBozELMAkG
A1UEBhMCUlUxEjAQBgNVBAgMCVRBVEFSU1RBTjEOMAwGA1UEBwwFS0FaQU4xEzAR
BgNVBAoMCkJBUlMgR3JvdXAxFzAVBgNVBAsMDkJBUlMtRWR1Y2F0aW9uMRUwEwYD
VQQDDAxiYXJzLW9wZW4ucnUxKzApBgkqhkiG9w0BCQEWHHRyc2FseWFodXRkaW5v
dkBiYXJzLW9wZW4ucnUwgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBANOz/iyz
a/WoMcNiSoJz8BGIcGmABzyya/kb74zVf8d+knDT/L7T8DiOct49EVn0Iz2wqP4P
JgPqV0Ag1gN8om9x+sZa1gj5+Cgl9fqMFFF2XHXOxNImsnpOHO5XGxV2wpceLtqh
pJFMiwlyK951ZTxCfMLgfp2ULrmBLW/LfGpnAgMBAAEwDQYJKoZIhvcNAQELBQAD
gYEAkCo2dC0IBFgmonMMuTo2Ef9aLwkwUbZAq8ZQ5Jv2ZBvvzN5XlmYfn2PC7rM8
9hKJPX+ISt2xdMGXVBiIxO7vdKDEvFd3GVHrSPCUXnDDRjzf3DZZlUlgE4gULJ3D
EWRc3pEwA8MPifzu1JNn3hmrhhcDi9K16YPStI/XfQ7a2Gw=
-----END CERTIFICATE-----\
"""


class HelloService(ServiceBase):

    @rpc(Unicode, Integer, _returns=Iterable(Unicode))
    def SayHello(ctx, Name, Times):
        return (u"Hello, {0}!".format(Name) for _ in xrange(Times))

security = X509TokenProfile(
    private_key=TEST_PRIVATE_KEY, private_key_pass="12345678",
    certificate=TEST_X509_CERT, digest_method="sha1")


application = Application(
    [HelloService], "http://example.com/hello-world-tns", "HelloWorld",
    in_protocol=Soap11WSSE(wsse_security=security),
    out_protocol=Soap11WSSE(wsse_security=security))

if __name__ == "__main__":
    wsgi_application = WsgiApplication(application)
    server = make_server("localhost", 8080, wsgi_application)
    server.serve_forever()