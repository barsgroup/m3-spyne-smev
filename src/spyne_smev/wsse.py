# -*- coding: utf-8 -*-

"""
wsse.py

:Created: 6/10/14
:Author: timic
"""
import logging
_logger = logging.getLogger(__name__)

from copy import deepcopy as _deepcopy
import uuid as _uuid
from lxml import etree as _etree

from spyne.model.fault import Fault as _Fault
from spyne.protocol.soap import Soap11 as _Soap11

import _crypto
import _utils
import _xmlns


class WSSecurity(object):

    def __init__(self, private_key_path, private_key_pass, certificate_path):
        self.private_key_path = private_key_path
        self.private_key_pass = private_key_pass
        self.certificate_path = certificate_path

    def apply(self, envelope):
        """
        Применяет профиль безопасности к конверту SOAP

        :param envelope: Soap конверт
        :return: Soap envelope with applied security
        """
        _logger.info("Attempt to sign document with key file {0}".format(
            self.private_key_path))
        unsigned = _deepcopy(envelope)
        try:
            return _sign_document(
                envelope, self.certificate_path,
                self.private_key_pass, self.private_key_path)
        except ValueError, e:
            _logger.error(
                "Error occurred while signing document:\n{0}\n"
                "Keep it unsigned ...".format(e.message))
            return unsigned

    @staticmethod
    def validate(envelope):
        """
        Проверяем, удовлетворяет ли конверт требованиям безопасности

        :param envelope: Soap конверт
        :raises: spyne.model.fault.Fault
        """
        is_valid = False
        _logger.info("Validate signed document")
        try:
            is_valid = _verify_document(envelope)
        except (_crypto.InvalidSignature, _crypto.Error, ValueError):
            _logger.error("Fault! Invalid signature.")

        if not is_valid:
            raise _Fault(
                'SMEV-100003', 'Invalid signature!')


class Soap11WSSE(_Soap11):
    """
    Протокол SOAP с поддержкой WS-Security

    :param wsse_security: Объек WS-Security
    :type wsse_security: wsfactory.spyne_smev.security.BaseWSSecurity
    """

    def __init__(
        self, app=None, validator=None, xml_declaration=True,
        cleanup_namespaces=True, encoding='UTF-8', pretty_print=False,
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
        if self.wsse_security:
            ctx.out_document = self.wsse_security.apply(ctx.out_document)
        super(Soap11WSSE, self).create_out_string(ctx, charset)


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
    binary_sec_token.text = certificate
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


def _sign_document(
        document, private_key_data, private_key_pass,
        cert_data, digest_name="md_gost94"):
    """
    Soap envelope signing according to SMEV recommendations

    :param document: Document to sign
    :type document: lxml.etree.Element
    :param unicode private_key_data: Private key text data
    :param unicode private_key_pass: Private key password
    :param unicode cert_data: Certificate text data
    :return: Signed document
    :rtype: lxml.etree.Element
    """
    nsmap = {
        "soap": _xmlns.soapenv,
        "wsse": _xmlns.wsse,
        "wsu": _xmlns.wsu,
        "ds": _xmlns.ds
    }
    header_node = document.find(
        "./{{{soap}}}Envelope/{{{soap}}}Header".format(**nsmap))

    if not header_node:
        header_node = _etree.Element("{{{soap}}}Header".format(**nsmap))
        document.insert(0, header_node)

    security_node = document.find(
        "{{{soap}}}}Envelope/{{{soap}}}Header/{{{wsse}}}}Security".format(
            **nsmap))

    if not security_node:
        wsse_header_node = _construct_wsse_header(certificate=cert_data)
        header_node.append(wsse_header_node)

    body_node = document.find("./{{{soap}}}Envelope/{{{soap}}}Body".format(
        **nsmap))
    body_id = "Id-%s" % str(_uuid.uuid4())
    body_node.attrib["{{{0}}}Id".format(_xmlns.wsu)] = body_id

    reference_node = document.find(
        "./{{{soap}}}:Envelope/{{{soap}}}:Header/{{{wsse}}}:Security/"
        "{{{ds}}}:Signature/{{{ds}}}:SignedInfo/{{{ds}}}:Reference".format(
            **nsmap))
    reference_node.attrib['URI'] = "#{0}".format(body_id)

    c14n_body_text = _etree.tostring(
        body_node, method='c14n', exclusive=True, with_comments=False)
    digest_value = _crypto.get_text_digest(c14n_body_text)

    digest_val_node = document.find(
        "./{{{soap}}}Envelope/{{{soap}}}Header/{{{wsse}}}Security"
        "/{{{ds}}}Signature/{{{ds}}}SignedInfo/{{{ds}}}Reference"
        "/{{{ds}}}DigestValue".format(
            **nsmap))
    digest_val_node.text = digest_value

    sign_info_node = document.find(
        "./{{{soap}}}Envelope/{{{soap}}}Header/{{{wsse}}}Security"
        "/{{{ds}}}Signature/{{{ds}}}SignedInfo".format(**nsmap))
    c14n_sign_info_text = _etree.tostring(
        sign_info_node, method='c14n', exclusive=True, with_comments=False)
    signature_value = _crypto.sign(
        c14n_sign_info_text, private_key_data, private_key_pass, digest_name)

    sign_val_node = document.find(
        "./{{{soap}}}Envelope/{{{soap}}}Header/{{{wsse}}}Security"
        "/{{{ds}}}Signature/{{{ds}}}SignatureValue".format(
            **nsmap))
    sign_val_node.text = signature_value

    return document


def _verify_document(document):
    pass