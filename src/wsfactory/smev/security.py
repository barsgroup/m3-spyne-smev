# -*- coding: utf-8 -*-
"""
security.py

:Created: 3/13/14
:Author: timic
"""

from lxml import etree
from spyne.model.fault import Fault

from libsmev.signer import (
    verify_envelope_signature, SignerError, sign_document)

from wsfactory.smev import xmlns as ns


class WSSecurity(object):

    def __init__(self, pem_file_name, private_key_pass):
        self.pem_file_name = pem_file_name
        self.private_key_pass = private_key_pass

    def apply(self, envelope):
        """
        Применяет профиль безопасности к конверту SOAP

        :param envelope: Soap конверт
        :return: Soap envelope with applied security
        """
        return sign_document(
            envelope, self.pem_file_name,
            self.private_key_pass, self.pem_file_name)

    def validate(self, envelope):
        """
        Проверяем, удовлетворяет ли конверт требованиям безопасности

        :param envelope: Soap конверт
        :raises: spyne.model.fault.Fault
        """
        is_valid = False
        try:
            is_valid = verify_envelope_signature(envelope)
        except SignerError:
            pass

        if not is_valid:
            raise Fault(
                'SMEV-100003', u'Неверная ЭП сообщения!')


def create_wsse_header(nsmap=None):
    root = etree.Element(
        '{%s}Security' % ns.wsse, nsmap=nsmap)
    root.attrib['{%s}actor' % ns.soapenv] = (
        'http://smev.gosuslugi.ru/actors/smev')
    token = etree.SubElement(
        root, '{%s}BinarySecurityToken' % ns.wsse)
    token.attrib['EncodingType'] = (
        "http://docs.oasis-open.org/wss/2004/01/"
        "oasis-200401-wss-soap-message-security-1.0#Base64Binary")
    token.attrib['ValueType'] = (
        "http://docs.oasis-open.org/wss/2004/01/"
        "oasis-200401-wss-x509-token-profile-1.0#X509v3")
    signature = etree.SubElement(root, '{%s}Signature' % ns.ds)
    signed_info = etree.SubElement(signature, '{%s}SignedInfo' % ns.ds)
    c14n_method = etree.SubElement(
        signed_info, '{%s}CanonicalizationMethod' % ns.ds)
    c14n_method.attrib['Algorithm'] = ns.c14n
    signature_method = etree.SubElement(
        signed_info, '{%s}SignatureMethod' % ns.ds)
    signature_method.attrib['Algorithm'] = ns.gostr3410
    ref = etree.SubElement(signed_info, '{%s}Reference' % ns.ds)
    transforms = etree.SubElement(ref, '{%s}Transforms' % ns.ds)
    transform = etree.SubElement(transforms, '{%s}Transform' % ns.ds)
    transform.attrib['Algorithm'] = ns.c14n
    digest_method = etree.SubElement(ref, '{%s}DigestMethod' % ns.ds)
    digest_method.attrib['Algorithm'] = ns.gostr3411hash
    etree.SubElement(ref, '{%s}DigestValue' % ns.ds)
    etree.SubElement(signature, '{%s}SignatureValue' % ns.ds)
    key_info = etree.SubElement(signature, '{%s}KeyInfo' % ns.ds)
    sec_token_ref = etree.SubElement(
        key_info, '{%s}SecurityTokenReference' % ns.wsse)
    token_ref = etree.SubElement(sec_token_ref, '{%s}Reference' % ns.wsse)
    token_ref.attrib['ValueType'] = (
        'http://docs.oasis-open.org/wss/2004/01/'
        'oasis-200401-wss-x509-token-profile-1.0#X509v3')
    return root