# -*- coding: utf-8 -*-

"""
client.py

:Created: 5/29/14
:Author: timic
"""
import logging as _logging
logger = _logging.getLogger(__name__)

from lxml import etree as _etree
from suds.client import Client as _SudsClient
from suds.plugin import MessagePlugin as _MessagePlugin
from suds.sax.parser import Parser as _Parser

from spyne_smev import wsse as _wsse, crypto as _crypto

IN = 1
OUT = 2
BOTH = 3


class Client(_SudsClient):
    """
    Клиент suds, в котором перекрыта возможность форматирования xml.
    Это необходимо для правильного вычисления подписей.
    Если в параметрах указаны путь к файлу с подпиcью и пароль, то запросы
    будут подписаны электронной подписью

    :param unicode pem_fn: Путь к файлу с ЭЦП
    :param unicode pem_pass: Пароль с ЭЦП
    """

    def __init__(
            self, url,
            private_key_path=None, private_key=None, private_key_pass=None,
            certificate_path=None, certificate=None, digest_name="md_gost94",
            security_direction=BOTH, **kwargs):
        kwargs["prettyxml"] = False

        self._private_key_path = private_key_path
        self._certificate_path = certificate_path
        self._certificate = certificate
        self._private_key = private_key
        self._digest_name = digest_name

        if self.certificate and self.private_key:
            self._smev_security = _WsseSecurity(
                self.private_key, private_key_pass, self.certificate,
                digest_name, security_direction)
            kwargs.setdefault("plugins", []).append(self._smev_security)
        super(Client, self).__init__(url, **kwargs)

    @property
    def private_key(self):
        if self._private_key is None:
            with open(self._private_key_path) as fd:
                self._private_key = fd.read()
        return self._private_key

    @property
    def certificate(self):
        if self._certificate is None:
            with open(self._certificate_path) as fd:
                self._certificate = fd.read()
        return self._certificate

    @property
    def last_verified(self):
        return self._smev_security.last_verified


class _WsseSecurity(_MessagePlugin):

    def __init__(self, private_key, private_key_password, certificate,
                 digest_name="md_gost94", direction=BOTH):

        if not direction in (IN, OUT, BOTH):
            raise ValueError(
                "direction should be constant either IN, OUT or BOTH!")

        self.private_key = private_key
        self.private_key_password = private_key_password
        self.certificate = certificate
        self.digest_name = digest_name
        self.direction = direction
        self._verified = None

    def marshalled(self, context):
        if self.direction in (OUT, BOTH):
            logger.debug("Signing document ...")

            document = _etree.fromstring(context.envelope.plain())
            try:
                _wsse.sign_document(
                    document, self.private_key, self.private_key_password,
                    self.certificate, self.digest_name)
            except Exception, e:
                logger.error("Cannot sign document")
                logger.exception(e)
                raise
            out_string = _etree.tostring(document, encoding="utf8")
            out_object = _Parser().parse(string=out_string)
            context.envelope.children = out_object.root().children

            logger.debug("Successfully signed")

    def received(self, context):
        if self.direction in (IN, BOTH):
            logger.debug("Verifying document ...")
            self._verified = False
            document = _etree.fromstring(context.reply)
            try:
                import ipdb; ipdb.set_trace()
                _wsse.verify_document(document, self.digest_name)
                self._verified = True
            except Exception, e:
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