# -*- coding: utf-8 -*-

"""
actions.py

:Created: 3/12/14
:Author: timic
"""

import objectpack

from models import Api, Protocol
import forms


class ApiPack(objectpack.ObjectPack):

    column_name_on_select = 'code'

    columns = [
        {
            'data_index': 'code',
            'header': u'Код',
            'width': 1,
        },
        {
            'data_index': 'description',
            'header': u'Описание',
            'width': 2
        }
    ]

    def declare_context(self, action):
        result = super(ApiPack, self).declare_context(action)
        if 'id' in result:
            result['id'] = {'type': 'str'}
        return result

    def get_rows_query(self, request, context):
        return Api.objects.configure()


class ServicePack(objectpack.ObjectPack):

    model = Service

    add_window = forms.ServiceAddWindow
    edit_window = forms.ServiceEditWindow

    columns = [
        {
            'data_index': 'code',
            'header': u'Код',
        },
        {
            'data_index': 'description',
            'header': u'Описание',
        }
    ]


class ServiceApiPack(objectpack.ObjectPack):

    model = ServiceApi
