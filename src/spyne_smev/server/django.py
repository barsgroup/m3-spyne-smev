# coding: utf-8
from __future__ import absolute_import

from spyne.server.django import DjangoApplication as _SpyneDjangoApplication

from spyne_smev.server import _AllYourInterfaceDocuments


class DjangoApplication(_SpyneDjangoApplication):

    # pylint: disable=abstract-method

    def __init__(self, app, chunked=True, max_content_length=2 * 1024 * 1024,
                 block_length=8 * 1024):
        super(DjangoApplication, self).__init__(
            app, chunked, max_content_length, block_length)
        self.doc = _AllYourInterfaceDocuments(app.interface)
