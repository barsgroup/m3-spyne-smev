# -*- coding: utf-8 -*-

"""
forms.py

:Created: 3/19/14
:Author: timic
"""

from m3.actions import ControllerCache
from m3_ext.ui import all_components as ext
import objectpack

from ..models import Service


class ServiceAddWindow(objectpack.ModelEditWindow):

    model = Service


class ServiceEditWindow(ServiceAddWindow):

    field_fabric_params = {

    }

    def _init_components(self):
        super(ServiceEditWindow, self)._init_components()
        self.service_api_grid = ext.ExtObjectGrid(
            title=u'Сервис-методы',
            layout='fit',
            region='center')

    def _do_layout(self):
        super(ServiceEditWindow, self)._do_layout()
        self.layout = 'border'
        self.form.region = 'north'
        self.items.append(self.service_api_grid)

    def set_params(self, params):
        super(ServiceEditWindow, self).set_params(params)
        ControllerCache.find_pack(
            'wsfactory.ui.actions.ServiceApiPack'
        ).configure_grid(self.service_api_grid)
