# -*- coding: utf-8 -*-

"""
models.py

:Created: 3/26/14
:Author: timic
"""

from spyne.model.primitive import Unicode, Integer, DateTime
from spyne.model.binary import File, BINARY_ENCODING_BASE64

from wsfactory.helpers import namespace
from wsfactory.smev.xmlns import smev256

with namespace(smev256) as ComplexModel:

    class OrgExternalType(ComplexModel):

        Code = Unicode(type_name="Code", pattern="[A-Z0-9]{4}\d{5}")
        Name = Unicode(type_name="Name")

    class ServiceType(ComplexModel):

        Mnemonic = Unicode(type_name="Mnemonic", min_occurs=1, max_occurs=1)
        Version = Unicode(
            type_name="Version", pattern="\d{1,2}\.\d{2}",
            min_occurs=1, max_occurs=1)

    class SubMessage(ComplexModel):

        SubRequestNumber = Unicode(type_name="SubRequestNumber",
                                   min_occurs=1, max_occurs=1)
        Status = Unicode(
            type_name="Status", min_occurs=1, max_occurs=1,
            values=("REQUEST", "RESULT", "REJECT", "INVALID", "ACCEPT", "PING",
                    "PROCESS", "NOTIFY", "FAILURE", "CANCEL", "STATE", "PACKET"))
        Originator = OrgExternalType(type_name="Originator", max_occurs=1)
        Date = DateTime(type_name="Date", min_occurs=1, max_occurs=1)
        RequestIdRef = Unicode(type_name="RequestIdRef", max_occurs=1)
        OriginRequestIdRef = Unicode(
            type_name="OriginRequestIdRef", max_occurs=1)
        ServiceCode = Unicode(type_name="ServiceCode", max_occurs=1)
        CaseNumber = Unicode(type_name="CaseNumber", max_occurs=1)

    class SubMessages(ComplexModel):

        SubMessage = SubMessage(
            type_name="SubMessage", min_occurs=1, max_occurs="unbounded")

    class MessageType(ComplexModel):

        Sender = OrgExternalType.customize(
            type_name="Sender", min_occurs=1, max_occurs=1)
        Recipient = OrgExternalType.customize(
            type_name="Recipient", min_occurs=1, max_occurs=1)
        Originator = OrgExternalType.customize(
            type_name="Originator", min_occurs=0, max_occurs=1)
        ServiceName = Unicode(
            type_name="ServiceName", max_occurs=1)
        Service = ServiceType.customize(
            type_name="Service", max_occurs=1)
        TypeCode = Unicode(
            type_name="TypeCode", values=["GSRV", "GFNC", "OTHR"],
            min_occurs=1, max_occurs=1)
        Status = Unicode(
            type_name="Status", values=["REQUEST", "RESPONSE"],
            min_occurs=1, max_occurs=1)
        Date = DateTime(type_name="Date", min_occurs=1, max_occurs=1)
        ExchangeType = Integer(type_name="ExchangeType", max_occurs=1)
        RequestIdRef = Unicode(type_name="RequestIdRef", max_occurs=1)
        OriginRequestIdRef = Unicode(
            type_name="OriginRequestIdRef", max_occurs=1)
        ServiceCode = Unicode(type_name="ServiceCode", max_occurs=1)
        CaseNumber = Unicode(type_name="CaseNumber", max_occurs=1)
        SubMessages = SubMessages(type_name="SubMessages", max_occurs=1)

    class HeaderType(ComplexModel):

        NodeId = Unicode(type_name="NodeId")
        MessageId = Unicode(type_name="MessageId")
        TimeStamp = DateTime(type_name="TimeStamp")
        MessageClass = Unicode(
            type_name="MessageClass",
            values=["REQUEST", "RESPONSE"])

    class AppDocument(ComplexModel):

        RequestCode = Unicode(type_name="RequestCode")
        BinaryData = File(
            type_name="BinaryData", encoding=BINARY_ENCODING_BASE64)