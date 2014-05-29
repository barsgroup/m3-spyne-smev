# -*- coding: utf-8 -*-

"""
client.py

:Created: 5/29/14
:Author: timic
"""
import logging
logger = logging.getLogger(__name__)

from lxml import etree
from suds.client import Client as SudsClient
from suds.plugin import MessagePlugin
from suds.sax.parser import Parser

from libsmev.signer import verify_envelope_signature, sign_document

IN = 1
OUT = 2
BOTH = 3


class Client(SudsClient):
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
            pem_fn=None, pem_pass=None, security_direction=BOTH,
            **kwargs):
        kwargs["prettyxml"] = False
        if pem_fn and pem_pass:
            self._smev_security = _SmevSecurity(
                pem_fn, pem_pass, security_direction)
            kwargs.setdefault("plugins", []).append(self._smev_security)
        super(Client, self).__init__(url, **kwargs)

    @property
    def last_verified(self):
        return self._smev_security.last_verified


class _SmevSecurity(MessagePlugin):

    def __init__(self, filename, password, direction=BOTH):

        if not direction in (IN, OUT, BOTH):
            raise ValueError(
                "direction should be constant either IN, OUT or BOTH!")

        self.filename = filename
        self.password = password
        self.direction = direction
        self._verified = None

    def marshalled(self, context):
        if self.direction in (OUT, BOTH):
            logger.debug("Signing document ...")

            document = etree.fromstring(context.envelope.plain())
            try:
                sign_document(document, self.filename, self.password)
            except Exception, e:
                logger.error("Cannot sign document!")
                logger.exception(e)
                raise
            out_string = etree.tostring(document, encoding="utf8")
            out_object = Parser().parse(string=out_string)
            context.envelope.children = out_object.root().children

            logger.debug("Successfully signed!")

    def received(self, context):
        if self.direction in (IN, BOTH):
            logger.debug("Verifying document ...")
            self._verified = False
            document = etree.fromstring(context.reply)
            try:
                self._verified = verify_envelope_signature(document)
            except Exception, e:
                logger.exception(e)
                raise
            finally:
                if self._verified:
                    logger.debug("Successfully verified!")
                else:
                    logger.error("Cannot verify!")

    @property
    def last_verified(self):
        return self._verified