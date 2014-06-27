# -*- coding: utf-8 -*-

"""
wsse.py

:Created: 6/10/14
:Author: timic
"""
import logging as _logging
logger = _logging.getLogger(__name__)
#TODO: add log messages

import base64 as _base64
from copy import deepcopy as _deepcopy
from functools import partial as _partial
import uuid as _uuid
from lxml import etree as _etree

from spyne.model.fault import Fault as _Fault
from spyne.protocol.soap import Soap11 as _Soap11

import crypto as _crypto
import _utils
import _xmlns
from _xmlns import nsmap as _nsmap


class BaseSecurity(object):

    def apply(self, envelope):
        raise NotImplementedError()

    def validate(self, envelope):
        raise NotImplementedError()


class WSSecurity(BaseSecurity):

    def __init__(
            self,
            private_key_path=None, private_key=None, private_key_pass=None,
            certificate_path=None, certificate=None, digest_name="md_gost94"):

        assert private_key_path or private_key, (
            "Either `private_key_path` or `private_key` should be defined")
        assert certificate_path or certificate, (
            "Either `certificate_path` or `certificate` should be defined")

        self._private_key_path = private_key_path
        self._private_key_pass = private_key_pass
        self._certificate_path = certificate_path
        self._certificate = certificate
        self._private_key = private_key
        self.digest_name = digest_name

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
                envelope, self.private_key,
                self._private_key_pass, self.certificate, self.digest_name)
        except ValueError, e:
            logger.error(
                "Error occurred while signing document:\n{0}\n"
                "Keep it unsigned ...".format(e.message))
            return unsigned

    def validate(self, envelope):
        """
        Проверяем, удовлетворяет ли конверт требованиям безопасности

        :param envelope: Soap конверт
        :raises: spyne.model.fault.Fault
        """
        logger.info("Validate signed document")
        try:
            verify_document(envelope, self.digest_name)
        except (_crypto.Error, ValueError), e:
            logger.error("Signature check failed! Error:\n{0}".format(
                unicode(e)))
            raise _Fault(
                faultstring="Signature check failed! Error:\n{0}".format(
                    unicode(e)))
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
            app, validator, xml_declaration,
            cleanup_namespaces, encoding, pretty_print)

    def create_in_document(self, ctx, charset=None):
        super(Soap11WSSE, self).create_in_document(ctx, charset)
        if self.wsse_security:
            in_document, _ = ctx.in_document
            self.wsse_security.validate(in_document)

    def create_out_string(self, ctx, charset=None):
        if self.wsse_security and ctx.method_name:
            ctx.out_document = self.wsse_security.apply(ctx.out_document)
        super(Soap11WSSE, self).create_out_string(ctx, charset)


_c14n = _partial(
    _etree.tostring, method="c14n", exclusive=True, with_comments=False)


def _construct_wsse_header(
        certificate, actor="http://smev.gosuslugi.ru/actors/smev"):

    soap = _utils.el_name_with_ns(_xmlns.soapenv)
    ds = _utils.el_name_with_ns(_xmlns.ds)
    wsse = _utils.el_name_with_ns(_xmlns.wsse)
    wsu = _utils.el_name_with_ns(_xmlns.wsu)

    root = _etree.Element(
        wsse("Security"),
        nsmap={
            "soapenv": _xmlns.soapenv,
            "wsse": _xmlns.wsse,
            "wsu": _xmlns.wsu,
            "ds": _xmlns.ds,
        },
        **{soap("actor"): actor})

    cert_id = "CertId-{0}".format(_uuid.uuid4().hex)
    binary_sec_token = _etree.SubElement(
        root, wsse("BinarySecurityToken"),
        EncodingType=_xmlns.base64enc,
        ValueType=_xmlns.x509_token_profile)
    binary_sec_token.attrib[wsu("Id")] = cert_id
    begin_marker = "-----BEGIN CERTIFICATE-----\n"
    end_marker = "\n-----END CERTIFICATE-----"
    begin_marker_pos = certificate.find(begin_marker)
    end_marker_pos = certificate.find(end_marker)
    if begin_marker_pos == -1 or end_marker_pos == -1:
        raise ValueError("Certificate doesnt contain BEGIN, END markers")
    clean_certificate = certificate[
        certificate.find(
            begin_marker) + len(begin_marker):certificate.find(end_marker)]
    binary_sec_token.text = clean_certificate

    signature = _etree.SubElement(root, ds("Signature"))
    signed_info = _etree.SubElement(signature, ds("SignedInfo"))
    _etree.SubElement(signature, ds("SignatureValue"))
    key_info = _etree.SubElement(signature, ds("KeyInfo"))
    _etree.SubElement(
        signed_info, ds("CanonicalizationMethod"),
        Algorithm=_xmlns.c14n)
    _etree.SubElement(
        signed_info, ds("SignatureMethod"),
        Algorithm="http://www.w3.org/2001/04/"
                  "xmldsig-more#gostr34102001-gostr3411")

    ref = _etree.SubElement(
        signed_info, ds("Reference"),
        URI="#body")
    transforms = _etree.SubElement(ref, ds("Transforms"))
    _etree.SubElement(
        transforms, ds("Transform"),
        Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
    _etree.SubElement(
        transforms, ds("Transform"),
        Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
    _etree.SubElement(
        ref, ds("DigestMethod"),
        Algorithm="http://www.w3.org/2001/04/xmldsig-more#gostr3411")
    _etree.SubElement(ref, ds("DigestValue"))

    sec_token_ref = _etree.SubElement(key_info, wsse("SecurityTokenReference"))
    _etree.SubElement(
        sec_token_ref, wsse("Reference"),
        URI=cert_id,
        ValueType=_xmlns.x509_token_profile)

    return root


def sign_document(
        document, private_key_data, private_key_pass,
        cert_data, digest_name="md_gost94"):
    """
    Soap envelope signing according to SMEV recommendations

    :param document: Document to sign
    :type document: lxml.etree.Element
    :param bytes private_key_data: Private key text data
    :param unicode private_key_pass: Private key password
    :param bytes cert_data: Certificate text data
    :return: Signed document
    :rtype: lxml.etree.Element
    """
    
    out_document = _deepcopy(document)
    header_node = out_document.find(
        "./{{{soapenv}}}Header".format(**_nsmap))
    if header_node is None:
        header_node = _etree.Element("{{{soapenv}}}Header".format(**_nsmap))
        out_document.insert(0, header_node)

    security_node = out_document.find(
        "./{{{soapenv}}}Header/{{{wsse}}}Security".format(**_nsmap))
    if not security_node:
        wsse_header_node = _construct_wsse_header(certificate=cert_data)
        header_node.append(wsse_header_node)

    body_node = out_document.find(
        "./{{{soapenv}}}Body".format(**_nsmap))
    body_id = "Id-%s" % str(_uuid.uuid4())
    body_node.attrib["{{{0}}}Id".format(_xmlns.wsu)] = body_id

    reference_node = out_document.find(
        "./{{{soapenv}}}Header/{{{wsse}}}Security/"
        "{{{ds}}}Signature/{{{ds}}}SignedInfo/{{{ds}}}Reference".format(
            **_nsmap))
    reference_node.attrib['URI'] = "#{0}".format(body_id)

    digest_value = _base64.b64encode(_crypto.get_text_digest(_c14n(body_node)))
    digest_val_node = out_document.find(
        "./{{{soapenv}}}Header/{{{wsse}}}Security"
        "/{{{ds}}}Signature/{{{ds}}}SignedInfo/{{{ds}}}Reference"
        "/{{{ds}}}DigestValue".format(**_nsmap))
    digest_val_node.text = digest_value

    sign_info_node = out_document.find(
        "./{{{soapenv}}}Header/{{{wsse}}}Security"
        "/{{{ds}}}Signature/{{{ds}}}SignedInfo".format(**_nsmap))
    c14n_sign_info_text = _etree.tostring(
        sign_info_node, method='c14n', exclusive=True, with_comments=False)
    signature_value = _base64.b64encode(_crypto.sign(
        c14n_sign_info_text, private_key_data, private_key_pass, digest_name))
    sign_val_node = out_document.find(
        "./{{{soapenv}}}Header/{{{wsse}}}Security"
        "/{{{ds}}}Signature/{{{ds}}}SignatureValue".format(**_nsmap))
    sign_val_node.text = signature_value

    return out_document


def verify_document(document, digest_name="md_gost94"):
    """
    Check SOAP envelope signature according to SMEV recommendations

    :param document: etree.Element XML Document
    :type document: lxml.etree.Element
    :param str digest_name: Digest method name (default GOST R 34.11-94)
    :raises: ValueError, spyne_smev.crypto.InvalidSignature
    """

    body = document.find("./{{{soapenv}}}Body".format(**_nsmap))
    if body is None:
        raise ValueError(
            "Incorrect soap envelope: "
            "`{{{soapenv}}}Body` tag not found".format(**_nsmap))

    digest_value = document.find(".//{{{ds}}}DigestValue".format(**_nsmap))
    if digest_value is None:
        raise ValueError(
            "Incorrect xmldsig structure: "
            "`{{{ds}}}DigestValue` tag not found".format(**_nsmap))

    binary_security_token = document.find(
        ".//{{{wsse}}}BinarySecurityToken".format(**_nsmap))
    if binary_security_token is None:
        raise ValueError(
            "Incorrect xmldsig structure: "
            "`{{{ds}}}BinarySecurityToken` tag not found".format(**_nsmap))

    signed_info = document.find(".//{{{ds}}}SignedInfo".format(**_nsmap))
    if signed_info is None:
        raise ValueError(
            "Incorrect xmldsig structure: "
            "`{{{ds}}}SignedInfo` tag not found".format(**_nsmap))

    signature = document.find(".//{{{ds}}}SignatureValue".format(**_nsmap))
    if signature is None:
        raise ValueError(
            "Incorrect xmldsig structure: "
            "`{{{ds}}}SignatureValue` tag not found".format(**_nsmap))

    body_digest = _base64.b64encode(_crypto.get_text_digest(
        _c14n(body),
        digest_name))

    if body_digest != digest_value.text:
        raise _crypto.InvalidSignature("Invalid `Body` digest!")

    _crypto.verify(
        _c14n(signed_info),
        "".join((
            "-----BEGIN CERTIFICATE-----\n",
            binary_security_token.text,
            "\n-----END CERTIFICATE-----"
        )),
        _base64.b64decode(signature.text),
        digest_name)