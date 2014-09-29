# README
* * *

## ABOUT

spyne-smev - это набор протоколов фреймворка [spyne](http://spyne.io/)
для работы с системой межведомственного электронного взаимодействия или просто
[СМЭВ](http://smev.gosuslugi.ru/).

Так же добавляет проверки безопасности в протокол Soap 1.1, основанные на рекомендацияx [WSSecurity](https://www.oasis-open.org/committees/download.php/16790/wss-v1.1-spec-os-SOAPMessageSecurity.pdf) (пока реализован только частично X509TokenProfile 1.1).
## REQUIREMENTS

* lxml (манипуляции с xml документами)
* cryptography (биндинг к libssl)
* spyne (необходим для работы протоколов spyne; необязательный, если нужен только клиент)
* suds (необходим только для работы клиента suds)

## INSTALLATION

* Сперва необходимо установить openssl и все сопутствующие ему библиотеки.
   Для различных операционных систем способ установки будет отличаться.

    Установка на Ubuntu:

        $ sudo apt-get install openssl libssl1.0.0 libssl-dev

* Установка библиотеки:

        $ pip install spyne-smev -i http://pypi.bars-open.ru/simple/

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
документации к [suds](https://fedorahosted.org/suds/wiki/Documentation).

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
* Клиент пока работает только с профилем безопасности x509 token profile.

## LICENCE

Copyright © 2014 ЗАО “БАРС Груп”

Данная лицензия разрешает лицам, получившим копию данного программного обеспечения и сопутствующей документации (в дальнейшем
именуемыми «Программное Обеспечение»), безвозмездно использовать Программное Обеспечение без ограничений, включая неограниченное
право на использование, копирование, изменение, добавление, публикацию, распространение, сублицензирование и/или продажу копий
Программного Обеспечения, также как и лицам, которым предоставляется данное Программное Обеспечение, при соблюдении следующих
условий:

Указанное выше уведомление об авторском праве и данные условия должны быть включены во все копии или значимые части данного
Программного Обеспечения.

ДАННОЕ ПРОГРАММНОЕ ОБЕСПЕЧЕНИЕ ПРЕДОСТАВЛЯЕТСЯ «КАК ЕСТЬ», БЕЗ КАКИХ-ЛИБО ГАРАНТИЙ, ЯВНО ВЫРАЖЕННЫХ ИЛИ ПОДРАЗУМЕВАЕМЫХ, ВКЛЮЧАЯ,
НО НЕ ОГРАНИЧИВАЯСЬ ГАРАНТИЯМИ ТОВАРНОЙ ПРИГОДНОСТИ, СООТВЕТСТВИЯ ПО ЕГО КОНКРЕТНОМУ НАЗНАЧЕНИЮ И ОТСУТСТВИЯ НАРУШЕНИЙ ПРАВ.
НИ В КАКОМ СЛУЧАЕ АВТОРЫ ИЛИ ПРАВООБЛАДАТЕЛИ НЕ НЕСУТ ОТВЕТСТВЕННОСТИ ПО ИСКАМ О ВОЗМЕЩЕНИИ УЩЕРБА, УБЫТКОВ ИЛИ ДРУГИХ ТРЕБОВАНИЙ 
ПО ДЕЙСТВУЮЩИМ КОНТРАКТАМ, ДЕЛИКТАМ ИЛИ ИНОМУ, ВОЗНИКШИМ ИЗ, ИМЕЮЩИМ ПРИЧИНОЙ ИЛИ СВЯЗАННЫМ С ПРОГРАММНЫМ ОБЕСПЕЧЕНИЕМ ИЛИ
ИСПОЛЬЗОВАНИЕМ ПРОГРАММНОГО ОБЕСПЕЧЕНИЯ ИЛИ ИНЫМИ ДЕЙСТВИЯМИ С ПРОГРАММНЫМ ОБЕСПЕЧЕНИЕМ.

Copyright © 2014 BARS Group

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.