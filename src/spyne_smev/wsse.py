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

from spyne.const import ansi_color as _color
from spyne.model.fault import Fault as _Fault
from spyne.protocol.soap import Soap11 as _Soap11

import crypto as _crypto
import _utils
import _xmlns
from _xmlns import nsmap as _nsmap


class BaseWSS(object):

    def apply(self, envelope):
        raise NotImplementedError()

    def validate(self, envelope):
        raise NotImplementedError()

_c14n_nsmap = {
    # (exclusive?, with_comments?): value
    (True, False): _xmlns.exc_c14n,
    (True, True): _xmlns.exc_c14n_wc,
    (False, False): _xmlns.xml_c14n,
    (False, True): _xmlns.xml_c14n_wc,
}

_c14n_params = dict((v, k) for k, v in _c14n_nsmap.iteritems())

_digest_method_nsmap = {
    "md_gost94": _xmlns.gost94,
    "sha1": _xmlns.sha1,
    "sha256": _xmlns.sha256,
    "sha512": _xmlns.sha512,
    "md5": _xmlns.md5,
}

_digest_method_names = dict((v, k) for k, v in _digest_method_nsmap.items())

_signature_method_nsmap = {
    "RSA-SHA1": _xmlns.rsa_sha1,
    "RSA-SHA256": _xmlns.rsa_sha256,
    "RSA-SHA512": _xmlns.rsa_sha512,
    "RSA-MD5": _xmlns.rsa_md5,
    "id-GostR3411-94-with-GostR3410-2001": _xmlns.gost2001,
}

_signature_method_names = dict(
    (v, k) for k, v in _signature_method_nsmap.items())

_signature_method_exclusions = {
    "id-GostR3411-94-with-GostR3410-2001": "md_gost94",
}


class X509TokenProfile(BaseWSS):

    def __init__(
            self,
            private_key_path=None, private_key=None, private_key_pass=None,
            certificate_path=None, certificate=None,
            digest_method="md_gost94",
            exclusive_c14n=True, c14n_with_comments=False,
            c14n_inclusive_prefixes=None):

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
        self._inclusive_prefixes = c14n_inclusive_prefixes

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
            verify_document(envelope, self.certificate)
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
        if self.log_messages:
            line_header = '%sRequest%s' % (
                _color.LIGHT_GREEN, _color.END_COLOR)
            in_string = list(ctx.in_string)
            if charset:
                xml_string = ''.join([s.decode(charset) for s in in_string])
            else:
                xml_string = ''.join(in_string)
            ctx.in_string = iter(in_string)
            logger.debug("%s %s" % (line_header, xml_string))
        super(Soap11WSSE, self).create_in_document(ctx, charset)
        if self.wsse_security:
            in_document, _ = ctx.in_document
            self.wsse_security.validate(in_document)

    def create_out_string(self, ctx, charset=None):
        if self.wsse_security and ctx.method_name:
            ctx.out_document = self.wsse_security.apply(ctx.out_document)
        super(Soap11WSSE, self).create_out_string(ctx, charset)


def _get_clean_cert_data(certificate):
    begin_marker = "-----BEGIN CERTIFICATE-----\n"
    end_marker = "\n-----END CERTIFICATE-----"
    begin_marker_pos = certificate.find(begin_marker)
    end_marker_pos = certificate.find(end_marker)
    if begin_marker_pos == -1 or end_marker_pos == -1:
        raise ValueError("Certificate doesnt contain BEGIN, END markers")
    return "".join(certificate[
        begin_marker_pos + len(begin_marker):end_marker_pos].split())


def _construct_wsse_header(
        certificate,
        actor="http://smev.gosuslugi.ru/actors/smev",
        digest_method="md_gost94",
        signature_method=None):
    digest_method_ns = _digest_method_nsmap.get(digest_method, None)
    if digest_method_ns is None:
        raise ValueError("No such digest method: {0}".format(digest_method))

    if not signature_method:
        signature_method = _crypto.get_signature_algorithm_name(certificate)
    signature_method_ns = _signature_method_nsmap.get(signature_method, None)
    if signature_method_ns is None:
        raise ValueError("No such signature method: {0}".format(signature_method))

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
    clean_certificate = _get_clean_cert_data(certificate)
    binary_sec_token.text = clean_certificate

    signature = _etree.SubElement(root, ds("Signature"))
    signed_info = _etree.SubElement(signature, ds("SignedInfo"))
    _etree.SubElement(signature, ds("SignatureValue"))
    key_info = _etree.SubElement(signature, ds("KeyInfo"))
    _etree.SubElement(
        signed_info, ds("CanonicalizationMethod"),
        Algorithm=_xmlns.exc_c14n)
    _etree.SubElement(
        signed_info, ds("SignatureMethod"),
        Algorithm=signature_method_ns)

    ref = _etree.SubElement(
        signed_info, ds("Reference"),
        URI="#body")
    transforms = _etree.SubElement(ref, ds("Transforms"))
    _etree.SubElement(
        transforms, ds("Transform"),
        Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
    _etree.SubElement(
        transforms, ds("Transform"),
        Algorithm=_xmlns.exc_c14n)
    _etree.SubElement(
        ref, ds("DigestMethod"),
        Algorithm=digest_method_ns)
    _etree.SubElement(ref, ds("DigestValue"))

    sec_token_ref = _etree.SubElement(key_info, wsse("SecurityTokenReference"))
    _etree.SubElement(
        sec_token_ref, wsse("Reference"),
        URI=cert_id,
        ValueType=_xmlns.x509_token_profile)

    return root


def sign_document(
        document, cert_data, pkey_data, pkey_pass,
        digest_method="md_gost94", c14n_exclusive=True,
        c14n_with_comments=False):
    """
    Soap envelope signing according to SMEV recommendations

    :param document: Document to sign
    :type document: lxml.etree.Element
    :param bytes pkey_data: Private key text data
    :param unicode pkey_pass: Private key password
    :param bytes cert_data: Certificate text data
    :return: Signed document
    :rtype: lxml.etree.Element
    """

    _c14n = _partial(
        _etree.tostring, method="c14n",
        exclusive=c14n_exclusive, with_comments=c14n_with_comments)

    out_document = _deepcopy(document)
    header_node = out_document.find(
        "./{{{soapenv}}}Header".format(**_nsmap))
    if header_node is None:
        header_node = _etree.Element("{{{soapenv}}}Header".format(**_nsmap))
        out_document.insert(0, header_node)

    security_node = out_document.find(
        "./{{{soapenv}}}Header/{{{wsse}}}Security".format(**_nsmap))
    if not security_node:
        wsse_header_node = _construct_wsse_header(
            certificate=cert_data, digest_method=digest_method)
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

    digest_value = _base64.b64encode(_crypto.get_text_digest(
        _c14n(body_node), digest_method))
    digest_val_node = out_document.find(
        "./{{{soapenv}}}Header/{{{wsse}}}Security"
        "/{{{ds}}}Signature/{{{ds}}}SignedInfo/{{{ds}}}Reference"
        "/{{{ds}}}DigestValue".format(**_nsmap))
    digest_val_node.text = digest_value

    sign_info_node = out_document.find(
        "./{{{soapenv}}}Header/{{{wsse}}}Security"
        "/{{{ds}}}Signature/{{{ds}}}SignedInfo".format(**_nsmap))
    signature_algorithm = _crypto.get_signature_algorithm_name(cert_data)
    signature_algorithm = _signature_method_exclusions.get(
        signature_algorithm, signature_algorithm)
    signature_value = _base64.b64encode(_crypto.sign(
        _c14n(sign_info_node), pkey_data, pkey_pass, signature_algorithm))
    sign_val_node = out_document.find(
        "./{{{soapenv}}}Header/{{{wsse}}}Security"
        "/{{{ds}}}Signature/{{{ds}}}SignatureValue".format(**_nsmap))
    sign_val_node.text = signature_value

    return out_document


def verify_document(document, certificate):
    """
    Check SOAP envelope signature according to SMEV recommendations

    :param document: etree.Element XML Document
    :type document: lxml.etree.Element
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

    if not binary_security_token.text == _get_clean_cert_data(certificate):
        raise ValueError("Incorrect binary security token")

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

    c14n = _partial(_etree.tostring, method="c14n")

    digest_method = document.find(".//{{{ds}}}DigestMethod".format(**_nsmap))
    if digest_method is None:
        raise ValueError(
            "Incorrect xmldsig structure: "
            "`{{{ds}}}DigestMethod` tag not found".format(**_nsmap))

    digest_name = _digest_method_names.get(
        digest_method.attrib["Algorithm"], None)
    if digest_name is None:
        raise ValueError(
            "Unsupported digest method algorithm: {0}".format(digest_name))

    transform = document.find(
        ".//{{{ds}}}Reference/{{{ds}}}Transforms/{{{ds}}}Transform".format(
            **_nsmap))
    if transform is None:
        raise ValueError(
            "Incorrect xmldsig structure: "
            "`{{{ds}}}Transform` tag not found".format(**_nsmap))
    c14n_method = transform.attrib["Algorithm"]
    exc_c14n, with_comments = _c14n_params.get(c14n_method)
    inc_ns = transform.find("{{{0}}}InclusiveNamespaces".format(
        _xmlns.exc_c14n))
    if not inc_ns is None:
        inc_ns_prefixes = inc_ns.attrib["PrefixList"].split()
        inc_ns_map = dict(
            (k, v) for k, v in document.nsmap.iteritems()
            if k in inc_ns_prefixes)
    else:
        inc_ns_map = None

    body_digest = _base64.b64encode(_crypto.get_text_digest(
        c14n(body, exclusive=exc_c14n, with_comments=with_comments,
             inclusive_ns_prefixes=inc_ns_map),
        digest_name))

    if body_digest != digest_value.text:
        raise _crypto.InvalidSignature("Invalid `Body` digest!")
    signature_method = document.find(
        ".//{{{ds}}}SignatureMethod".format(**_nsmap))
    if signature_method is None:
        raise ValueError(
            "Incorrect xmldsig structure: "
            "`{{{ds}}}SignatureMethod` tag not found".format(**_nsmap))
    digest_name = _signature_method_names.get(
        signature_method.attrib["Algorithm"], None)
    if digest_name is None:
        raise ValueError(
            "Unsupported signature method algorithm: {0}".format(
                signature_method.attrib["Algorithm"]))
    digest_name = _signature_method_exclusions.get(digest_name, digest_name)

    c14n_method_node = document.find(
        ".//{{{ds}}}CanonicalizationMethod".format(**_nsmap))
    if c14n_method_node is None:
        raise ValueError(
            "Incorrect xmldsig structure: "
            "`{{{ds}}}CanonicalizationMethod` tag not found".format(**_nsmap))
    c14n_method = c14n_method_node.attrib["Algorithm"]
    exc_c14n, with_comments = _c14n_params.get(c14n_method)
    inc_ns = c14n_method_node.find("{{{0}}}InclusiveNamespaces".format(
        _xmlns.exc_c14n))
    if not inc_ns is None:
        inc_ns_prefixes = inc_ns.attrib["PrefixList"].split()
        inc_ns_map = dict(
            (k, v) for k, v in document.nsmap.iteritems()
            if k in inc_ns_prefixes)
    else:
        inc_ns_map = None
    _crypto.verify(
        c14n(signed_info, exclusive=exc_c14n, with_comments=with_comments,
             inclusive_ns_prefixes=inc_ns_map),
        certificate,
        _base64.b64decode(signature.text),
        digest_name)