# coding: utf-8
from __future__ import absolute_import

import logging as _logging

from lxml import etree as _etree
from suds.client import Client as _SudsClient
from suds.plugin import MessagePlugin as _MessagePlugin
from suds.sax.parser import Parser as _Parser

from spyne_smev import crypto as _crypto
from spyne_smev.wsse import utils as _utils


logger = _logging.getLogger(__name__)


class Client(_SudsClient):
    """
    Suds client which supports digital signing with XMLDSIG messages via
    x509 token profile

    :param unicode private_key_path: File path to private key
    :param unicode private_key_path: Private key passphrase
    :param bytes private_key: Private key (either this or
                               private_key_path required)
    :param unicode certificate_path: File path to X509 certificate
    :param bytes certificate: Certificate (either this or
                               certificate_path required)
    :param unicode incoming_certificate_path: File path to certificate which
                                               allowed in incoming message
    :param bytes incoming_certificate: Incoming certificate

    """

    IN = 1
    OUT = 2
    BOTH = 3

    def __init__(
            self, url,
            private_key_path=None, private_key=None, private_key_pass=None,
            certificate_path=None, certificate=None,
            in_certificate_path=None, in_certificate=None,
            digest_method="sha1",
            security_direction=BOTH, **kwargs):

        if security_direction not in (self.IN, self.OUT, self.BOTH):
            raise ValueError(
                "direction should be constant either IN, OUT or BOTH!")

        kwargs["prettyxml"] = False

        self._private_key_path = private_key_path
        self._certificate_path = certificate_path
        self._certificate = certificate
        self._private_key = private_key
        self._in_certificate_path = in_certificate_path
        self._in_certificate = in_certificate
        self._digest_method = digest_method
        self._security = None

        if not any((self._in_certificate, self._in_certificate_path)):
            self._in_certificate = self.certificate

        if self.certificate and self.private_key:
            # pylint: disable=protected-access
            self._security = _WsseSecurity(
                self.private_key, private_key_pass or _crypto._ffi.NULL,
                self.certificate, self.in_certificate,
                digest_method, security_direction)
            kwargs.setdefault("plugins", []).append(self._security)
        super(Client, self).__init__(url, **kwargs)

    @property
    def private_key(self):
        if self._private_key is None and self._private_key_path:
            with open(self._private_key_path) as fd:
                self._private_key = fd.read()
        return self._private_key

    @property
    def certificate(self):
        if self._certificate is None and self._certificate_path:
            with open(self._certificate_path) as fd:
                self._certificate = fd.read()
        return self._certificate

    @property
    def in_certificate(self):
        if self._in_certificate is None and self._in_certificate_path:
            with open(self._in_certificate_path) as fd:
                self._in_certificate = fd.read()
        return self._in_certificate

    @property
    def last_verified(self):
        if self._security:
            return self._security.last_verified


class _WsseSecurity(_MessagePlugin):

    def __init__(self, private_key, private_key_password, certificate,
                 in_certificate, digest_method, direction=Client.BOTH):

        self.private_key = private_key
        self.private_key_password = private_key_password
        self.certificate = certificate
        self.in_certificate = in_certificate
        self.digest_method = digest_method
        self.direction = direction
        self._verified = None

    def marshalled(self, context):
        if self.direction in (Client.OUT, Client.BOTH):
            logger.debug("Signing document ...")
            document = _etree.fromstring(context.envelope.plain())
            try:
                out_document = _utils.sign_document(
                    document, self.certificate, self.private_key,
                    self.private_key_password, self.digest_method)
            except Exception as e:
                logger.error("Cannot sign document")
                logger.exception(e)
                raise
            out_string = _etree.tostring(out_document, encoding="utf8")
            out_object = _Parser().parse(string=out_string)
            context.envelope.children = out_object.root().children

            logger.debug("Successfully signed")

    def received(self, context):
        if self.direction in (Client.IN, Client.BOTH):
            logger.debug("Verifying document ...")
            self._verified = False
            document = _etree.fromstring(context.reply)
            try:
                _utils.verify_document(document, self.in_certificate)
                self._verified = True
            except Exception as e:
                logger.exception(e)
                raise
            finally:
                if self._verified:
                    logger.debug("Successfully verified")
                else:
                    logger.error("Verify failed")

    @property
    def last_verified(self):
        return self._verified
