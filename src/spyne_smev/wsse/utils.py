# coding: utf-8
from __future__ import absolute_import

from copy import deepcopy as _deepcopy
from functools import partial as _partial
import base64 as _base64
import uuid as _uuid

from lxml import etree as _etree
import six

from spyne_smev import _utils
from spyne_smev import _xmlns
from spyne_smev import crypto as _crypto


_nsmap = _xmlns.nsmap

_c14n_nsmap = {
    # (exclusive?, with_comments?): value
    (True, False): _xmlns.exc_c14n,
    (True, True): _xmlns.exc_c14n_wc,
    (False, False): _xmlns.xml_c14n,
    (False, True): _xmlns.xml_c14n_wc,
}

_c14n_params = dict(
    (v, k) for k, v in six.iteritems(_c14n_nsmap)
)


_digest_method_nsmap = {
    "md_gost94": _xmlns.gost94,
    "md_gost12_256": _xmlns.md_gost2012_256,
    "md_gost12_512": _xmlns.md_gost2012_512,
    "sha1": _xmlns.sha1,
    "sha256": _xmlns.sha256,
    "sha512": _xmlns.sha512,
    "md5": _xmlns.md5,
}

_digest_method_names = dict(
    (v, k) for k, v in six.iteritems(_digest_method_nsmap)
)

_signature_method_nsmap = {
    "RSA-SHA1": _xmlns.rsa_sha1,
    "RSA-SHA256": _xmlns.rsa_sha256,
    "RSA-SHA512": _xmlns.rsa_sha512,
    "RSA-MD5": _xmlns.rsa_md5,
    "id-GostR3411-94-with-GostR3410-2001": _xmlns.gost2001,
    "id-tc26-signwithdigest-gost3410-2012-256": _xmlns.gost2012_256,
    "id-tc26-signwithdigest-gost3410-2012-512": _xmlns.gost2012_512,
}

_signature_method_names = dict(
    (v, k) for k, v in _signature_method_nsmap.items())

_signature_method_exclusions = {
    "id-GostR3411-94-with-GostR3410-2001": "md_gost94",
    "id-tc26-signwithdigest-gost3410-2012-256": "md_gost12_256",
    "id-tc26-signwithdigest-gost3410-2012-512": "md_gost12_512",
}


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
        digest_method="sha1",
        signature_method=None):
    # pylint: disable=too-many-locals
    digest_method_ns = _digest_method_nsmap.get(digest_method, None)
    if digest_method_ns is None:
        raise ValueError("No such digest method: {0}".format(digest_method))

    if not signature_method:
        signature_method = _crypto.get_signature_algorithm_name(certificate)
    signature_method_ns = _utils.get_dict_value(
        _signature_method_nsmap,
        signature_method
    )
    if signature_method_ns is None:
        raise ValueError(
            "No such signature method: {0}".format(signature_method))

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
        Algorithm=_xmlns.exc_c14n)
    _etree.SubElement(
        ref, ds("DigestMethod"),
        Algorithm=digest_method_ns)
    _etree.SubElement(ref, ds("DigestValue"))

    sec_token_ref = _etree.SubElement(key_info, wsse("SecurityTokenReference"))
    _etree.SubElement(
        sec_token_ref, wsse("Reference"),
        URI="#{0}".format(cert_id),
        ValueType=_xmlns.x509_token_profile)

    return root


def sign_document(
        document, cert_data, pkey_data, pkey_pass,
        digest_method="sha1", c14n_exclusive=True,
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
    # pylint: disable=too-many-locals
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
    signature_algorithm = _utils.get_dict_value(
        _signature_method_exclusions,
        signature_algorithm,
        signature_algorithm
    )
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
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
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
    if inc_ns is not None:
        inc_ns_prefixes = inc_ns.attrib["PrefixList"].split()
        inc_ns_map = dict(
            (k, v) for k, v in six.iteritems(document.nsmap)
            if k in inc_ns_prefixes)
    else:
        inc_ns_map = None

    body_digest = _base64.b64encode(_crypto.get_text_digest(
        c14n(body, exclusive=exc_c14n, with_comments=with_comments,
             inclusive_ns_prefixes=inc_ns_map),
        digest_name))

    if body_digest.decode() != digest_value.text:
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
    if inc_ns is not None:
        inc_ns_prefixes = inc_ns.attrib["PrefixList"].split()
        inc_ns_map = dict(
            (k, v) for k, v in six.iteritems(document.nsmap)
            if k in inc_ns_prefixes)
    else:
        inc_ns_map = None
    _crypto.verify(
        c14n(signed_info, exclusive=exc_c14n, with_comments=with_comments,
             inclusive_ns_prefixes=inc_ns_map),
        certificate,
        _base64.b64decode(signature.text),
        digest_name)
