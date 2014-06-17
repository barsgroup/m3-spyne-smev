# -*- coding: utf-8 -*-

"""
_base.py

:Created: 5/13/14
:Author: timic
"""
import logging

from spyne_smev import _xmlns as ns


logger = logging.getLogger(__name__)

from lxml import etree

from spyne.interface.wsdl.wsdl11 import Wsdl11
from spyne.model.fault import Fault

from _utils import load_schema, load_xml, Cap, copy_with_nsmap
from wsse import Soap11WSSE


class ApiError(Fault):
    """
    Специальный exception, который может быть возбужден в api-методе.

    Специальным образом обрабатывается в потомках исходящего протокола
    Soap11WSSE: вместо Fault в body soap-конверта кладется вызываемый
    soap-message c элементом Error внутри.

    В остальных протоколах вёдет себя как обычный Fault

    TODO: пока необходимо явно передавать имя api-метода в котором возбуждается
    исключение
    """

    detail = None
    faultactor = "Server"

    def __init__(
            self, errorCode, errorMessage, messageName):
        self.errorCode = errorCode
        self.errorMessage = errorMessage
        self.messageName = messageName

    @property
    def faultcode(self):
        return self.errorCode

    @property
    def faultstring(self):
        return self.errorMessage

    def __repr__(self):
        return u"Error(%s: %s)" % (self.errorCode, self.errorMessage)


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
            ctx.udc = Cap()
        ctx.udc.in_smev_header_document = in_document.find(
            ".//{%(spyne_smev)s}Header" % self._ns)
        ctx.udc.in_smev_message_document = in_document.find(
            ".//{%(spyne_smev)s}Message" % self._ns)
        ctx.udc.in_smev_appdoc_document = in_document.find(
            ".//{%(spyne_smev)s}AppDocument" % self._ns)
        message_data = in_document.find(
            ".//{%(spyne_smev)s}MessageData" % self._ns)
        if not all((ctx.udc.in_smev_message_document, message_data)):
            raise Fault("SMEV-100010", "Invalid configuration!")
        map(self._validate_smev_element, filter(bool, (
            ctx.udc.in_smev_message_document,
            ctx.udc.in_smev_header_document,
            message_data)))
        method_data = message_data.find(
            ".//{%(spyne_smev)s}AppData" % self._ns).getchildren()
        method = in_document.find(
            ".//{%s}Body" % ns.soapenv).getchildren()[0]
        method.clear()
        method.extend(method_data)
        self.event_manager.fire_event('smev_in_document_built', ctx)

    def deserialize(self, ctx, message):
        super(BaseSmev, self).deserialize(ctx, message)
        self.create_in_smev_objects(ctx)
        self.event_manager.fire_event('create_in_smev_objects', ctx)

    def serialize(self, ctx, message):
        super(BaseSmev, self).serialize(ctx, message)
        if ctx.out_error is None or issubclass(
                ctx.out_error.__class__, ApiError):
            self.construct_smev_envelope(ctx, message)

    def _validate_smev_element(self, element):
        self._smev_schema = self._smev_schema or load_schema(
            self._smev_schema_path)
        if not self._smev_schema.validate(element):
            errors = "\n".join((
                err.message for err in self._smev_schema.error_log))
            raise Fault(
                "SMEV-102000",
                "Message didn't pass validation checks! Errors:\n%s" % errors)

    def to_parent_element(self, cls, value, tns, parent_elt, *args, **kwargs):
        if issubclass(cls, ApiError):
            message = etree.SubElement(
                parent_elt, "{%s}%s" % (tns, value.messageName))
            error = etree.SubElement(message, "{%s}%s" % (tns, "Error"))
            etree.SubElement(
                error, "{%s}%s" % (tns, "errorCode")
            ).text = value.errorCode
            etree.SubElement(
                error, "{%s}%s" % (tns, "errorMessage")
            ).text = value.errorMessage
        else:
            super(BaseSmev, self).to_parent_element(
                cls, value, tns, parent_elt, *args, **kwargs)

    def construct_smev_envelope(self, ctx, message):
        """
        Оборачивает soap-конверт в СМЭВ-сообщение
        """
        raise NotImplementedError()

    def create_in_smev_objects(self, ctx):
        raise NotImplementedError()


class BaseSmevWsdl(Wsdl11):

    smev_schema_path = None
    smev_ns = None

    __smev_schema = None

    def __init__(self, interface=None, _with_partnerlink=False):
        super(BaseSmevWsdl, self).__init__(interface, _with_partnerlink)
        self._ns = self.interface.nsmap.copy()
        self._ns.update({'spyne_smev': self.smev_ns})

    def _get_smev_schema(self):
        self.__smev_schema = self.__smev_schema or load_xml(
            self.smev_schema_path)
        return self.__smev_schema

    def build_interface_document(self, url):
        super(BaseSmevWsdl, self).build_interface_document(url)
        smev_schema = self._get_smev_schema().getroot()
        smev_schema = copy_with_nsmap(smev_schema, dict(tns=self._ns["tns"]))
        messages = self.root_elt.xpath(
            "./wsdl:portType/wsdl:operation/wsdl:input/@message | "
            "./wsdl:portType/wsdl:operation/wsdl:output/@message",
            namespaces=self._ns)
        messages = tuple(message.split(':') for message in messages)
        for _, message in messages:
            self._create_message_schema(smev_schema, message)

        tns_schema = self.root_elt.find(
            "./{%(wsdl)s}types/{%(xs)s}schema[@targetNamespace='%(tns)s']"
            % self._ns)
        new_tns_schema = copy_with_nsmap(tns_schema, {'spyne_smev': self.smev_ns})

        for _, message in messages:
            element = new_tns_schema.find(
                './/{%s}element[@name="%s"]' % (ns.xs, message))
            element.attrib['type'] = 'spyne_smev:%sType' % message

        self.root_elt.find("./{%s}types" % ns.wsdl).insert(0, smev_schema)
        tns_schema.getparent().replace(tns_schema, new_tns_schema)

        self._add_smev_headers(self.root_elt)
        self._Wsdl11__wsdl = etree.tostring(
            self.root_elt, encoding='UTF-8')

    def _create_message_schema(self, schema, message):
        root = etree.SubElement(
            schema, "{%(xs)s}complexType" % self._ns,
            name="%sType" % message)
        seq = etree.SubElement(root, "{%(xs)s}sequence" % self._ns)
        etree.SubElement(
            seq, "{%(xs)s}element" % ns.nsmap256,
            name="Message", type="spyne_smev:MessageType")
        message_data = etree.SubElement(
            seq, "{%(xs)s}element" % ns.nsmap256, name="MessageData")
        complex_type = etree.SubElement(
            message_data, "{%(xs)s}complexType" % self._ns)
        seq = etree.SubElement(complex_type, "{%(xs)s}sequence" % self._ns)
        etree.SubElement(
            seq, "{%(xs)s}element" % self._ns,
            name="AppData", type="tns:%s" % message, minOccurs="0")
        etree.SubElement(
            seq, "{%(xs)s}element" % self._ns,
            name="AppDocument", type="spyne_smev:AppDocumentType", minOccurs="0")
        return root

    def _add_smev_headers(self, wsdl):
        operations = wsdl.xpath(
            "./wsdl:binding/wsdl:operation/wsdl:input | "
            "./wsdl:binding/wsdl:operation/wsdl:output",
            namespaces=self._ns)

        header_message = etree.Element(
            "{%(wsdl)s}message" % self._ns, name='SmevHeader')
        message_pos = wsdl.index(wsdl.findall(
            './{%(wsdl)s}message' % self._ns)[-1])
        wsdl.insert(message_pos, header_message)

        etree.SubElement(
            header_message, "{%(wsdl)s}part" % self._ns,
            nsmap={'spyne_smev': self.smev_ns},
            name="SmevHeader", element="spyne_smev:Header")

        for operation in operations:
            binding = operation.getparent().getparent().find(
                "{%(soap)s}binding" % self._ns)
            style = binding.attrib['style']
            header = operation.find("./{%(soap)s}header" % self._ns)
            if header and style == 'document':
                binding['style'] = 'rpc'
            etree.SubElement(
                operation, "{%(soap)s}header" % self._ns,
                nsmap={'spyne_smev': self.smev_ns},
                message='tns:SmevHeader',
                part='SmevHeader',
                use='literal')