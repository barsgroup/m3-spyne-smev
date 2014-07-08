# README
* * *

## ABOUT

spyne-smev - это набор протоколов фреймворка [spyne](http://spyne.io/>)
для работы с системой межведомственного электронного взаимодействия или просто
[СМЭВ](http://smev.gosuslugi.ru/>).

## REQUIREMENTS

* lxml (манипуляции с xml документами)
* cryptography (биндинг к libssl)
* spyne (необходим для работы протоколов spyne)
* suds (необходим только для работы клиента suds)

## INSTALLATION

1. Сперва необходимо установить openssl и все сопутствующие ему библиотеки.
   Для различных операционных систем способ установки будет отличаться.

    Установка на Ubuntu:

        $ sudo apt-get install openssl libssl1.0.0 libssl-dev

1. Установка зависимостей

        $ pip install https://github.com/timic/cryptography/archive/0.4.1.zip#egg=cryptography


1. Установка библиотеки:

        $ pip install https://bitbucket.org/barsgroup/spyne-smev/get/tip.tar.gz

## Использование

spyne-smev предоставляет набор классов расширяющих возможности базового протокола
фреймворка spyne - `Soap11`.

### WS-Security

`Soap11Wsse` - базовый протокол. Расширяет класс `Soap11`.
Добавляет в него функционал позволяющий применить некий профиль безопасности
к исходящему сообщению, и выполнить валидацию входящего в соответсвии с
этим профилем. Эти действия делегируются классу-наследнику
`BaseWSSProfile`, который соответственно должен реализовать два метода:
`apply` и `verify`.

`X509TokenProfile`, профиль который реализует механизм подписи
[XMLDSIG](http://www.w3.org/TR/xmldsig-core) по спецификации
[x509 token profile](http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0.pdf).

Пример создания django view для сервиса с применением подписи XMLDSIG:

    from spyne.application import Application
    from spyne.decorator import rpc
    from spyne.server.django import DjangoApplication
    from spyne.service import ServiceBase
    from spyne.model.primitive import Integer

    from spyne_smev.wsse.protocols import Soap11WSSE, X509TokenProfile


    class GetSumService(ServiceBase):

        @rpc(Integer, Integer, _returns=Integer, _body_style="bare")
        def Sum(ctx, A, B):
            return A + B

    in_security =  out_security = X509TokenProfile(
        private_key=pkey,
        private_key_pass=pkey_pass,
        certificate=cert,
        digest_method="sha1")
    in_protocol = Soap11WSSE(wsse_security=in_security)
    out_protocol = Soap11WSSE(wsse_security=out_security)

    application = Application(
        [GetSumService], "http://my-domain.site/tns",
        in_protocol=in_protocol,
        out_protocol=out_protocol)
    service_view = DjangoApplication(application)


### СМЭВ

По [методическим рекомендациям](http://smev.gosuslugi.ru/portal/api/files/get/27403)
СМЭВ все сообщения должны быть подписаны электронной подписью.
Класс `BaseSmev` расширяет протокол `Soap11WSSE`, таким образом, что
при формировании ответа, содержимое soap message встраивается в блок элемента
СМЭВ MessageData/AppData, а при разборе входящего наоборот, содержимое AppData
вставляется в Body сообщения, а элементы СМЭВ Header, Message и AppDocument
выкидывается из сообщения, разбираются отдельно и записываются в контекст
spyne в специальный объект udc (user defined data).

Пример:

    from spyne.decorator import rpc
    from spyne.service import ServiceBase
    from spyne.model.primitive import Integer, Unicode
    from spyne.model.complex import Iterable

    from spyne_smev.application import Application
    from spyne_smev.server.django import DjangoApplication
    from spyne_smev.smev256 import Smev256
    from spyne_smev.wsse.protocols import X509TokenProfile


    class PingSmevService(ServiceBase):

        @rpc(Integer, _returns=Iterable(Unicode))
        def Ping(ctx, Times):
            return (
                "Hello {0}! You requested service {1} with version {2}".format(
                    ctx.udc.in_smev_message.Sender.Name,
                    ctx.udc.in_smev_message.Service.Mnemonic,
                    ctx.udc.in_smev_message.Service.Version)
                for _ in xrange(Times)
            )

    in_security = out_security = X509TokenProfile(
        private_key=pkey,
        private_key_pass=pkey_pass,
        certificate=cert,
        digest_method="sha1")

    in_protocol = Smev256(wsse_security=in_security)
    out_protocol = Smev256(
        wsse_security=out_security,
        SenderCode="123456789",
        SenderName="EDUPORTAL",
        RecipientCode="987654321",
        RecipientName="GOVPORTAL",
        Mnemonic="123456789",
        Version="1.00")

    application = Application(
        [PingSmevService], "http://my-domain.site/tns",
        in_protocol=in_protocol,
        out_protocol=out_protocol)
    service_view = DjangoApplication(application)


*Регистрация сервиса с валидной СМЭВ-схемой в wsdl требует использования
классов `Application`, `WsgiApplication` и `DjangoApplication` из библиотеки
spyne_smev вместо spyne. Это поведение в дальнейшем может изменится.*

### Клиент

В качестве клиента используется suds с небольшими дополнениями, речь о которых
пойдет дальше. О том как устроен и работает suds можно почитать в официальной
документации к [suds](link_to_suds_documentation).

В классе `spyne_smev.client.Client` запрещено форматирование `prettyxml`,
а так же добавлен плагин подписи и верификации сообщений, работающий аналогично
профилю `X509TokenProfile`.

Примеры:

    # для сервиса GetSumService
    from spyne_smev.client import Client

    client = Client(
        "http://url_to_get_sum_service?wsdl",
        private_key=pkey, private_key_pass=pkey_pass,
        certificate=cert, in_certificate=cert, digest_method="sha1")

    response = client.service.Sum(A=3, B=5)
    if client.last_verified:
        print("A + B =", response.Sum)
        # 8
    else:
        raise ValueError("Response signature didn't pass validation")


    # для сервиса PingSmevService
    client = Client(
        "http://url_to_ping_smev_service?wsdl",
        private_key=pkey, private_key_pass=pkey_pass,
        certificate=cert, in_certificate=cert, digest_method="sha1")
    msg = client.factory.create("Ping")
    msg.Message.Sender.Name = "PORTAL"
    msg.Message.Service.Mnemonic = "123456789"
    msg.Message.Service.Version = "0.34"
    msg.MessageData.AppData.Times = 3

    # чтобы пример не был большим остальные атрибуты были пропущены
    ...

    result = client.service.Ping(msg.Message, msg.MessageData)
    print("\n".join(result.MessageData.AppData.Iterable))
    # Hello PORTAL! You requested service 123456789 with version 0.34
    # Hello PORTAL! You requested service 123456789 with version 0.34
    # Hello PORTAL! You requested service 123456789 with version 0.34


Подробные примеры можно посмотреть
[тут](https://bitbucket.org/barsgroup/spyne-smev/src/tip/src/examples/?at=default).

## LIMITATIONS

* Поддерживается только протокол СМЭВ версии 2.5.6
* Пока не поддерживаются ссылки на вложения в AppDocument, а так же не
  реализовано api для упаковки файлов в BinaryData согласно рекомендациям
  (пока все делаем ручками)

## LICENCE