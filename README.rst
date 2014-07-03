ABOUT
=====

spyne-smev - это набор протоколов фреймворка `spyne <http://spyne.io/>`_
для работы с системой межведомственного электронного взаимодействия или просто
`СМЭВ <http://smev.gosuslugi.ru/>`_.


REQUIREMENTS
============

* spyne - если
* cryptography (биндинг к libssl для подписывания цифровой подписью конверторв soap)
* suds (необходим только для работы клиента)


INSTALLATION
============

#. Сперва необходимо установить openssl и все сопутствующие ему библиотеки.
   Для различных операционных систем способ установки будет отличаться.

   Установка на Ubuntu::

    $ sudo apt-get install openssl libssl1.0.0 libssl-dev


#.

#. Установка библиотеки::

    $ pip install https://bitbucket.org/barsgroup/spyne-smev/get/tip.tar.gz


USAGE
=====


WS-Security
-----------


Smev protocol
-------------


CLIENT
------


LICENCE
=======
