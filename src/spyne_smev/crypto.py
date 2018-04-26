# coding: utf-8
from __future__ import absolute_import

from functools import partial as _partial
import logging as _logging

from cryptography.hazmat.bindings.openssl.binding import Binding as _Binding
from six import text_type

from . import _utils


logger = _logging.getLogger(__name__)
# TODO: add log messages


_binding = _Binding()
_lib, _ffi = _binding.lib, _binding.ffi
_openssl_configured = False
if not _openssl_configured:
    _lib.OPENSSL_config(_ffi.NULL)
    _openssl_configured = True


class InvalidSignature(Exception):
    """
    An error occurred if message signature
    """


class Error(Exception):
    """
    An error occurred in an `libcrypto` API.
    """


def _exception_from_error_queue(exception_type):
    def text(charp):
        return _utils.native(_ffi.string(charp))

    errors = []
    while True:
        error = _lib.ERR_get_error()
        if error == 0:
            break
        errors.append((
            text(_lib.ERR_lib_error_string(error)),
            text(_lib.ERR_func_error_string(error)),
            text(_lib.ERR_reason_error_string(error))))

    raise exception_type(errors)


_raise_current_error = _partial(_exception_from_error_queue, Error)


def get_text_digest(text, digest_name=b"sha1"):
    """
    Returns binary digest value for given text.

    :param basestring text: Text for digest processing
    :param str digest_name: Digest algorithm name
    :return str: text digest
    """
    if isinstance(digest_name, text_type):
        digest_name = digest_name.encode('utf-8')
    evp_md = _lib.EVP_get_digestbyname(digest_name)

    if evp_md == _ffi.NULL:
        raise ValueError("No such digest method")

    evp_md_ctx = _lib.Cryptography_EVP_MD_CTX_new()
    if _lib.EVP_DigestInit_ex(evp_md_ctx, evp_md, _ffi.NULL) == 0:
        _raise_current_error()

    input_buffer = _utils.byte_string(text)

    if _lib.EVP_DigestUpdate(evp_md_ctx, input_buffer, len(input_buffer)) == 0:
        _raise_current_error()

    result_buf = _ffi.new("char[]", _lib.EVP_MAX_MD_SIZE)
    result_len = _ffi.new("unsigned int[]", 1)
    result_len[0] = len(result_buf)
    if _lib.EVP_DigestFinal_ex(evp_md_ctx, result_buf, result_len) == 0:
        _raise_current_error()

    _lib.Cryptography_EVP_MD_CTX_free(evp_md_ctx)

    return b"".join(_ffi.buffer(result_buf, result_len[0]))


def sign(
        data, pkey_buffer, pkey_pass=_ffi.NULL, digest_name="sha1"):
    """
    Sign data with private key. Returns binary signature

    :param unicode data: Data to sign
    :param bytes pkey_buffer: Private key
    :param unicode pkey_pass: Private key's passphrase
    :param str digest_name: Message digest method
    :return bytes: Signature
    """

    md = _lib.EVP_get_digestbyname(_utils.byte_string(digest_name))
    if md == _ffi.NULL:
        raise ValueError("No such digest method: {0}".format(digest_name))

    md_ctx = _lib.Cryptography_EVP_MD_CTX_new()

    if _lib.EVP_SignInit(md_ctx, md) != 1:
        _raise_current_error()
    if _lib.EVP_SignUpdate(md_ctx, data, len(data)) != 1:
        _raise_current_error()

    signature_buffer = _ffi.new("unsigned char []", 512)
    signature_length = _ffi.new("unsigned int *")
    signature_length[0] = len(signature_buffer)
    pkey = _load_private_key(pkey_buffer, pkey_pass)
    final_result = _lib.EVP_SignFinal(
        md_ctx, signature_buffer, signature_length, pkey)

    if final_result != 1:
        _raise_current_error()

    return _ffi.buffer(signature_buffer, signature_length[0])[:]


def verify(data, cert_data, signature, digest_name="sha1"):
    """
    Verifies text signature with certificate. Raises InvalidSignature in case
    of signature is not correct and Error if internal openssl error occurred.

    :param basestring data: Signed data
    :param basestring cert_data: Certificate
    :param basestring signature: Binary signature of data
    :param str digest_name: Digest method name
    :raises: ValueError, spyne_smev.crypto.InvalidSignature,
              spyne_smev.crypto.Error
    """
    md = _lib.EVP_get_digestbyname(_utils.byte_string(digest_name))

    if md == _ffi.NULL:
        raise ValueError("No such digest method")

    md_ctx = _ffi.new("EVP_MD_CTX*")
    md_ctx = _ffi.gc(md_ctx, _lib.EVP_MD_CTX_cleanup)

    if _lib.EVP_VerifyInit(md_ctx, md) == 0:
        _raise_current_error()

    if _lib.EVP_VerifyUpdate(md_ctx, data, len(data)) == 0:
        _raise_current_error()

    cert = _load_certificate(cert_data)
    pkey = _get_cert_pub_key(cert)
    if pkey == _ffi.NULL:
        _raise_current_error()

    result = _lib.EVP_VerifyFinal(
        md_ctx, signature, len(signature), pkey)

    if result == -1:
        _raise_current_error()
    elif result == 0:
        raise InvalidSignature("Invalid signature")


def _new_mem_buf(buf=None):

    if buf is None:
        bio = _lib.BIO_new(_lib.BIO_s_mem())
        free = _lib.BIO_free
    else:
        data = _ffi.new("char[]", buf)
        bio = _lib.BIO_new_mem_buf(data, len(buf))

        def free(bio, ref=data):
            return _lib.BIO_free(bio)

    if bio == _ffi.NULL:
        _raise_current_error()

    bio = _ffi.gc(bio, free)

    return bio


def _load_certificate(buf):

    if isinstance(buf, _utils.text_type):
        buf = buf.encode("ascii")

    bio = _new_mem_buf(buf)
    x509 = _lib.PEM_read_bio_X509(bio, _ffi.NULL, _ffi.NULL, _ffi.NULL)

    if x509 == _ffi.NULL:
        _raise_current_error()

    return _ffi.gc(x509, _lib.X509_free)


def _get_cert_pub_key(x509):

    pkey = _lib.X509_get_pubkey(x509)

    if pkey == _ffi.NULL:
        _raise_current_error()

    return _ffi.gc(pkey, _lib.EVP_PKEY_free)


def _load_private_key(pem_buffer, pass_phrase=_ffi.NULL):

    if isinstance(pem_buffer, _utils.text_type):
        pem_buffer = pem_buffer.encode("ascii")

    if isinstance(pass_phrase, _utils.text_type):
        pass_phrase = pass_phrase.encode("ascii")

    bio = _new_mem_buf(pem_buffer)

    evp_pkey = _lib.PEM_read_bio_PrivateKey(
        bio, _ffi.NULL, _ffi.NULL, pass_phrase)

    if evp_pkey == _ffi.NULL:
        _raise_current_error()

    return _ffi.gc(evp_pkey, _lib.EVP_PKEY_free)


def get_signature_algorithm_name(certificate):

    cert = _load_certificate(certificate)
    digest_nid = _lib.X509_get_signature_nid(cert)
    if digest_nid == _lib.NID_undef:
        raise ValueError("Unsupported certificate signature algorithm")

    digest_name = _lib.OBJ_nid2sn(digest_nid)
    if digest_name == _ffi.NULL:
        _raise_current_error()

    return _ffi.string(digest_name)
