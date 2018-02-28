# coding: utf-8
from __future__ import absolute_import

import logging as _logging
import os

from lxml import etree as _etree
from six.moves import map
from spyne.const.http import HTTP_200
from spyne.interface.wsdl.wsdl11 import Wsdl11 as _Wsdl11
from spyne.model.fault import Fault as _Fault
import six

from . import _utils
from . import _xmlns as _ns
from .fault import ApiError as _ApiError
from .wsse.protocols import Soap11WSSE


logger = _logging.getLogger(__name__)


class BaseSmev(Soap11WSSE):
    """
    Базовый класс для протоколов СМЭВ

    .. note::
        Конкретные реализации протоколов должны перегрузить методы
        :func:`create_in_smev_objects` и :func:`construct_smev_envelope`

    :param smev_params: Словарь с параметрами для СМЭВ
    """
    _smev_schema_path = None
    _ns = None
    _interface_document_type = None

    def __init__(
            self, app=None, validator=None, xml_declaration=True,
            cleanup_namespaces=True, encoding='UTF-8', pretty_print=False,
            wsse_security=None, **smev_params):
        super(BaseSmev, self).__init__(
            app, validator, xml_declaration,
            cleanup_namespaces, encoding,
            pretty_print, wsse_security)
        self.smev_params = smev_params or {}
        self._smev_schema = None

    def create_in_document(self, ctx, charset=None):
        super(BaseSmev, self).create_in_document(ctx, charset)
        in_document, _ = ctx.in_document
        if ctx.udc is None:
            ctx.udc = _utils.EmptyCtx()
        ctx.udc.in_smev_header_document = in_document.find(
            ".//{{{smev}}}Header".format(**self._ns))
        ctx.udc.in_smev_message_document = in_document.find(
            ".//{{{smev}}}Message".format(**self._ns))
        ctx.udc.in_smev_appdoc_document = in_document.find(
            ".//{{{smev}}}AppDocument".format(**self._ns))
        message_data = in_document.find(
            ".//{{{smev}}}MessageData".format(**self._ns))

        if any(map(_utils.isnone,
                   (ctx.udc.in_smev_message_document, message_data))):
            raise _Fault("SMEV-100010", "Invalid configuration!")

        for element in (ctx.udc.in_smev_message_document,
                        ctx.udc.in_smev_header_document,
                        message_data):
            if element is not None:
                self._validate_smev_element(element)

        method_data = message_data.find(
            ".//{{{smev}}}AppData".format(**self._ns)).getchildren()
        method = in_document.find(
            ".//{{{0}}}Body".format(_ns.soapenv)).getchildren()[0]
        method.clear()
        method.extend(method_data)
        self.event_manager.fire_event('smev_in_document_built', ctx)

    def deserialize(self, ctx, message):
        super(BaseSmev, self).deserialize(ctx, message)
        self.create_in_smev_objects(ctx)
        self.event_manager.fire_event('create_in_smev_objects', ctx)

    def serialize(self, ctx, message):
        super(BaseSmev, self).serialize(ctx, message)
        if ctx.out_error is None or isinstance(ctx.out_error, _ApiError):
            self.construct_smev_envelope(ctx, message)
            self.event_manager.fire_event("after_serialize_smev", ctx)

    def _validate_smev_element(self, element):
        self._smev_schema = self._smev_schema or _utils.load_schema(
            self._smev_schema_path)
        if not self._smev_schema.validate(element):
            errors = "\n".join((
                err.message for err in self._smev_schema.error_log))
            raise _Fault(
                "SMEV-102000",
                "Message didn't pass validation checks!"
                " Errors:\n{0}".format(errors))

    # method version for spyne<2.11.0
    def to_parent_element(self, cls, value, tns, parent_elt, *args, **kwargs):
        if issubclass(cls, _ApiError):
            message = _etree.SubElement(
                parent_elt, "{{{0}}}{1}".format(tns, value.messageName))
            error = _etree.SubElement(
                message, "{{{0}}}{1}".format(tns, "Error")
            )
            _etree.SubElement(
                error, "{{{0}}}{1}".format(tns, "errorCode")
            ).text = value.errorCode

            if not isinstance(value.errorMessage, six.text_type):
                error_msg = value.errorMessage.decode('UTF-8')
            else:
                error_msg = value.errorMessage

            _etree.SubElement(
                error, "{{{0}}}{1}".format(tns, "errorMessage")
            ).text = error_msg
        else:
            super(BaseSmev, self).to_parent_element(
                cls, value, tns, parent_elt, *args, **kwargs)

    # method version for spyne>=2.11.0
    def to_parent(self, ctx, cls, inst, parent, ns, *args, **kwargs):
        if issubclass(cls, _ApiError):
            message = _etree.SubElement(
                parent, "{{{0}}}{1}".format(ns, inst.messageName))
            error = _etree.SubElement(
                message, "{{{0}}}{1}".format(ns, "Error")
            )
            _etree.SubElement(
                error, "{{{0}}}{1}".format(ns, "errorCode")
            ).text = inst.errorCode

            if not isinstance(inst.errorMessage, six.text_type):
                error_msg = inst.errorMessage.decode('UTF-8')
            else:
                error_msg = inst.errorMessage

            _etree.SubElement(
                error, "{{{0}}}{1}".format(ns, "errorMessage")
            ).text = error_msg
        else:
            return super(BaseSmev, self).to_parent(
                ctx, cls, inst, parent, ns, *args, **kwargs)

    def construct_smev_envelope(self, ctx, message):
        """
        Оборачивает soap-конверт в СМЭВ-сообщение
        """
        raise NotImplementedError()

    def create_in_smev_objects(self, ctx):
        raise NotImplementedError()

    def fault_to_http_response_code(self, fault):
        if isinstance(fault, _ApiError):
            return HTTP_200
        return super(BaseSmev, self).fault_to_http_response_code(fault)


class BaseSmevWsdl(_Wsdl11):

    smev_schema_path = None
    smev_ns = None

    __smev_schema = None

    def __init__(self, interface=None, _with_partnerlink=False):
        super(BaseSmevWsdl, self).__init__(interface, _with_partnerlink)
        self._ns = self.interface.nsmap.copy()
        self._ns.update({'smev': self.smev_ns})

    def _get_smev_schema(self):
        self.__smev_schema = self.__smev_schema or _utils.load_xml(
            self.smev_schema_path)
        return self.__smev_schema

    def build_interface_document(self, url):
        super(BaseSmevWsdl, self).build_interface_document(url)
        smev_schema = self._get_smev_schema().getroot()
        smev_schema = _utils.copy_with_nsmap(
            smev_schema, dict(tns=self._ns["tns"]))

        messages = self.root_elt.xpath(
            "./wsdl:portType/wsdl:operation/wsdl:input/@message | "
            "./wsdl:portType/wsdl:operation/wsdl:output/@message",
            namespaces=self._ns)
        messages = tuple(message.split(':') for message in messages)
        for _, message in messages:
            self._create_message_schema(smev_schema, message)

        tns_schema = self.root_elt.find(
            "./{{{wsdl}}}types/{{{xs}}}schema[@targetNamespace='{tns}']"
            .format(**self._ns))
        new_tns_schema = _utils.copy_with_nsmap(
            tns_schema, {'smev': self.smev_ns})

        # importing smev schema into tns, required
        # for compatibility with suds client
        new_tns_schema.insert(0, _etree.Element(
            "{{{xs}}}import".format(**self._ns), namespace=self.smev_ns))

        for _, message in messages:
            element = new_tns_schema.find(
                './/{{{0}}}element[@name="{1}"]'.format(_ns.xs, message))
            element.attrib['type'] = 'smev:{0}Type'.format(message)

        self.root_elt.find(
            "./{{{0}}}types".format(_ns.wsdl)).insert(0, smev_schema)
        tns_schema.getparent().replace(tns_schema, new_tns_schema)

        import_xop_include = smev_schema.find(
            "{{{0}}}import"
            "[@namespace='http://www.w3.org/2004/08/xop/include']"
            .format(_ns.xs)
        )
        if import_xop_include is not None:
            import_xop_include.attrib.pop("schemaLocation")
            xop_include_schema = _utils.load_xml(
                os.path.join(
                    os.path.dirname(__file__), "xsd", "xop-include.xsd")
            ).getroot()
            self.root_elt.find("./{{{0}}}types".format(_ns.wsdl)).insert(
                0, xop_include_schema)

        self._add_smev_headers(self.root_elt)
        # pylint: disable=attribute-defined-outside-init
        self._Wsdl11__wsdl = _etree.tostring(
            self.root_elt, encoding='UTF-8')

    def _create_message_schema(self, schema, message):
        root = _etree.SubElement(
            schema, "{{{xs}}}complexType".format(**self._ns),
            name="{0}Type".format(message))
        seq = _etree.SubElement(root, "{{{xs}}}sequence".format(**self._ns))
        _etree.SubElement(
            seq, "{{{xs}}}element".format(**_ns.nsmap256),
            name="Message", type="smev:MessageType")
        message_data = _etree.SubElement(
            seq, "{{{xs}}}element".format(**_ns.nsmap256), name="MessageData")
        complex_type = _etree.SubElement(
            message_data, "{{{xs}}}complexType".format(**self._ns))
        seq = _etree.SubElement(
            complex_type, "{{{xs}}}sequence".format(**self._ns))
        _etree.SubElement(
            seq, "{{{xs}}}element" .format(**self._ns),
            name="AppData", type="tns:{0}".format(message), minOccurs="0")
        _etree.SubElement(
            seq, "{{{xs}}}element".format(**self._ns),
            name="AppDocument", type="smev:AppDocumentType", minOccurs="0")
        return root

    def _add_smev_headers(self, wsdl):
        operations = wsdl.xpath(
            "./wsdl:binding/wsdl:operation/wsdl:input | "
            "./wsdl:binding/wsdl:operation/wsdl:output",
            namespaces=self._ns)

        header_message = _etree.Element(
            "{{{wsdl}}}message".format(**self._ns), name="SmevHeader")
        message_pos = wsdl.index(wsdl.findall(
            './{{{wsdl}}}message'.format(**self._ns))[-1])
        wsdl.insert(message_pos, header_message)

        _etree.SubElement(
            header_message, "{{{wsdl}}}part".format(**self._ns),
            nsmap={"smev": self.smev_ns},
            name="SmevHeader", element="smev:Header")

        for operation in operations:
            binding = operation.getparent().getparent().find(
                "{{{soap}}}binding".format(**self._ns))
            style = binding.attrib['style']
            header = operation.find("./{{{soap}}}header".format(**self._ns))
            if header and style == 'document':
                binding['style'] = 'rpc'
            _etree.SubElement(
                operation, "{{{soap}}}header".format(**self._ns),
                nsmap={"smev": self.smev_ns},
                message="tns:SmevHeader",
                part="SmevHeader",
                use="literal")
