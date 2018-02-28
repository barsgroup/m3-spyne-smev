# coding: utf-8
from __future__ import absolute_import

from copy import deepcopy as _deepcopy
import logging as _logging

from spyne.const import ansi_color as _color
from spyne.model.fault import Fault as _Fault
from spyne.protocol.soap import Soap11 as _Soap11
import six

from spyne_smev import crypto as _crypto
from spyne_smev.wsse.utils import _c14n_nsmap
from spyne_smev.wsse.utils import sign_document
from spyne_smev.wsse.utils import verify_document


logger = _logging.getLogger(__name__)
# TODO: add log messages


class BaseWSS(object):

    def apply(self, envelope):
        raise NotImplementedError()

    def validate(self, envelope):
        raise NotImplementedError()


class X509TokenProfile(BaseWSS):

    def __init__(
            self,
            private_key_path=None, private_key=None, private_key_pass=None,
            certificate_path=None, certificate=None,
            digest_method="sha1",
            exclusive_c14n=True, c14n_with_comments=False):

        assert private_key_path or private_key, (
            "Either `private_key_path` or `private_key` should be defined")
        assert certificate_path or certificate, (
            "Either `certificate_path` or `certificate` should be defined")

        self._private_key_path = private_key_path
        self._private_key_pass = private_key_pass
        self._certificate_path = certificate_path
        self._certificate = certificate
        self._private_key = private_key
        self.digest_method = digest_method

        self._c14n = _c14n_nsmap.get((exclusive_c14n, c14n_with_comments))

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

    def apply(self, envelope):
        """
        Применяет профиль безопасности к конверту SOAP

        :param envelope: Soap конверт
        :return: Soap envelope with applied security
        """
        logger.info("Signing document ...")
        unsigned = _deepcopy(envelope)
        try:
            return sign_document(
                envelope, self.certificate, self.private_key,
                self._private_key_pass, self.digest_method)
        except ValueError as e:
            logger.error('\n'.join((
                'Error occurred while signing document:',
                six.text_type(e),
                'Keep it unsigned...'
            )))
            return unsigned

    def validate(self, envelope):
        """
        Проверяем, удовлетворяет ли конверт требованиям безопасности

        :param envelope: Soap конверт
        :raises: spyne.model.fault.Fault
        """
        logger.info("Validate signed document")
        try:
            verify_document(envelope, self.certificate)
        except (_crypto.Error, ValueError) as e:
            logger.error(
                "Signature check failed! Error:\n%s", six.text_type(e)
            )
            raise _Fault(faultstring=(
                "Signature check failed! Error:\n" + six.text_type(e)
            ))
        except _crypto.InvalidSignature:
            raise _Fault(faultstring="Invalid signature!")


class Soap11WSSE(_Soap11):
    """
    Протокол SOAP с поддержкой WS-Security

    :param wsse_security: Объек WS-Security
    :type wsse_security: wsfactory.spyne_smev.security.BaseWSSecurity
    """

    def __init__(
        self, app=None, validator=None, xml_declaration=True,
        cleanup_namespaces=True, encoding="UTF-8", pretty_print=False,
        wsse_security=None,
    ):
        self.wsse_security = wsse_security
        if self.wsse_security:
            pretty_print = False
        super(Soap11WSSE, self).__init__(
            app=app, validator=validator, xml_declaration=xml_declaration,
            cleanup_namespaces=cleanup_namespaces, encoding=encoding,
            pretty_print=pretty_print)

    def create_in_document(self, ctx, charset=None):
        if logger.level == _logging.DEBUG:
            line_header = '%sRequest%s' % (
                _color.LIGHT_GREEN, _color.END_COLOR)
            in_string = list(ctx.in_string)
            if charset:
                xml_string = ''.join([s.decode(charset) for s in in_string])
            else:
                xml_string = ''.join(in_string)
            ctx.in_string = iter(in_string)
            logger.debug("%s %s", line_header, xml_string)
        super(Soap11WSSE, self).create_in_document(ctx, charset)
        if self.wsse_security:
            in_document, _ = ctx.in_document
            self.wsse_security.validate(in_document)

    def create_out_string(self, ctx, charset=None):
        if self.wsse_security and ctx.method_name:
            ctx.out_document = self.wsse_security.apply(ctx.out_document)
        super(Soap11WSSE, self).create_out_string(ctx, charset)
