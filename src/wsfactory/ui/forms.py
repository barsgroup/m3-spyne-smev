# -*- coding: utf-8 -*-

"""
forms.py

:Created: 3/19/14
:Author: timic
"""
from django.utils.translation import ugettext as _

import objectpack
from m3_ext.ui import all_components as ext
from objectpack.ui import make_combo_box


class ServiceEditWindow(objectpack.BaseEditWindow):

    def _init_components(self):
        super(ServiceEditWindow, self)._init_components()
        self.code_field = ext.ExtStringField(
            label=_(u"Код"),
            name="code",
            allow_blank=False,
            anchor="100%")
        self.name_field = ext.ExtStringField(
            label=_(u"Наименование"),
            name="name",
            allow_blank=False,
            anchor="100%")
        self.api_json_field = ext.ExtStringField(
            name="api_json",
            hidden=True)
        self.hash_field = ext.ExtStringField(
            name="hash",
            hidden=True)
        self.api_grid = ext.ExtObjectGrid(
            header=True,
            title=_(u"Сервис-методы"),
            height=200,
            anchor="100%")

    def _do_layout(self):
        super(ServiceEditWindow, self)._do_layout()
        self.form.items.extend((
            self.code_field,
            self.name_field,
            self.api_json_field,
        ))

        self.items.append(self.api_grid)

    def set_params(self, params):
        super(ServiceEditWindow, self).set_params(params)
        self.template_globals = "ui-js/service-edit-window.js"
        self.auto_height = True
        self.api_grid.allow_paging = False
        self.api_grid.add_column(
            data_index="code",
            header=_(u"Код"))
        self.api_grid.add_column(
            data_index="name",
            header=_(u"Наименование"))
        self.api_grid.top_bar.items.extend((
            ext.ExtButton(
                text=_(u"Добавить"),
                icon_cls="add_item",
                handler="addApi"),
            ext.ExtButton(
                text=_(u"Удалить"),
                icon_cls="delete_item",
                handler="deleteApi")))
        self.api_grid.store = ext.ExtDataStore()
        self.api_grid.store.load_data(params["object"].api_data)
        self.api_grid.store._listeners.update({
            "add": "onApiEditing",
            "remove": "onApiEditing"})
        self.select_api_url = params["select_api_url"]


class SecurityEditWindow(objectpack.BaseEditWindow):

    def _init_components(self):
        super(SecurityEditWindow, self)._init_components()
        self.code_field = ext.ExtStringField(
            label=_(u"Код"),
            name="code",
            allow_blank=False,
            anchor="100%")
        self.name_field = ext.ExtStringField(
            label=_(u"Наименование"),
            name="name",
            allow_blank=False,
            anchor="100%")
        self.pem_file_path_field = ext.ExtStringField(
            label=_(u"Путь к файлу с подписью"),
            name="pem_file_name",
            allow_blank=False,
            anchor="100%")
        self.priv_key_pass_field = ext.ExtStringField(
            label=_(u"Пароль к подписи"),
            name="private_key_pass",
            input_type="password",
            allow_blank=False,
            anchor="100%")
        self.hash_field = ext.ExtStringField(
            name="hash",
            hidden=True)

    def _do_layout(self):
        super(SecurityEditWindow, self)._do_layout()
        self.form.items.extend((
            self.code_field,
            self.name_field,
            self.pem_file_path_field,
            self.priv_key_pass_field,
            self.hash_field,
        ))

    def set_params(self, params):
        super(SecurityEditWindow, self).set_params(params)
        self.height = "auto"


class ApplicationEditWindow(objectpack.BaseEditWindow):

    def _init_components(self):
        super(ApplicationEditWindow, self)._init_components()
        self.container = ext.ExtContainer(layout="form", anchor="100%")
        self.name_field = ext.ExtStringField(
            name="name",
            label=_(u"Код"),
            allow_blank=False,
            anchor="100%")
        self.service_field = make_combo_box(
            name="service",
            label=_(u"Услуга"),
            allow_blank=False,
            anchor="100%")
        self.in_protocol_field_set = ext.ExtFieldSet(anchor="100%")
        self.out_protocol_field_set = ext.ExtFieldSet(anchor="100%")
        self.in_protocol_field = make_combo_box(
            name="in_protocol",
            label=_(u"Вх. протокол"),
            allow_blank=False,
            anchor="100%")
        self.in_security_field = make_combo_box(
            name="in_security",
            label=_(u"Профиль безопасности"),
            allow_blank=True,
            anchor="100%")
        self.out_protocol_field = make_combo_box(
            name="out_protocol",
            label=_(u"Исх. протокол"),
            allow_blank=False,
            anchor="100%")
        self.out_security_field = make_combo_box(
            name="out_security",
            label=_(u"Профиль безопасности"),
            allow_blank=True,
            anchor="100%")
        self.hash_field = ext.ExtStringField(name="hash", hidden=True)
        self.in_protocol_param_json_field = ext.ExtStringField(
            name="in_protocol_params_json", hidden=True)
        self.out_protocol_param_json_field = ext.ExtStringField(
            name="out_protocol_params_json", hidden=True)
        self.in_protocol_param_grid = self._make_param_grid(
            _(u"Параметры протокола"), self.in_protocol_param_json_field)
        self.out_protocol_param_grid = self._make_param_grid(
            _(u"Параметры протокола"), self.out_protocol_param_json_field)

    def _do_layout(self):
        super(ApplicationEditWindow, self)._do_layout()
        self.form.items.append(self.container)
        self.container.items.extend((
            self.name_field,
            self.service_field))
        self.form.items.extend((
            self.in_protocol_field_set,
            self.out_protocol_field_set,
        ))
        self.in_protocol_field_set.items.append(
            container(
                self.in_protocol_field,
                self.in_security_field,
                layout="form", anchor="100%"))
        self.out_protocol_field_set.items.append(
            container(
                self.out_protocol_field,
                self.out_security_field,
                layout="form", anchor="100%"))
        self.form.items.append(self.hash_field)
        self.form.items.extend((
            self.in_protocol_param_json_field,
            self.out_protocol_param_json_field,
        ))
        self.in_protocol_field_set.items.append(
            container(
                self.in_protocol_param_grid,
                layout="form", label_align="top"))
        self.out_protocol_field_set.items.append(
            container(
                self.out_protocol_param_grid,
                layout="form", label_align="top"))

    def set_params(self, params):
        super(ApplicationEditWindow, self).set_params(params)
        self.service_field.data = params["services"]
        self.in_protocol_field.data = params["in_protocols"]
        self.out_protocol_field.data = params["out_protocols"]
        self.in_security_field.data = params["security"]
        self.out_security_field.data = params["security"]
        self.auto_height = True
        self.form.layout = "auto"
        self.in_protocol_param_grid.store.load_data(
            params["object"].in_protocol_params_data)
        self.out_protocol_param_grid.store.load_data(
            params["object"].out_protocol_params_data)
        self.template_globals = "ui-js/application-edit-window.js"

    @staticmethod
    def _make_param_grid(label, json_field):
        grid = ext.ExtObjectGrid(
            label=label, height=140)
        grid.add_column(
            header=_(u"Имя"), data_index="key",
            editor=ext.ExtStringField(allow_blank=False))
        grid.add_column(
            header=_(u"Значение"), data_index="value",
            editor=ext.ExtStringField(allow_blank=False))
        grid.add_column(
            header=_(u"Тип значения"), data_index="value_type",
            editor=make_combo_box(
                allow_blank=False,
                data=(
                    ("str", "str"),
                    ("unicode", "unicode"),
                    ("int", "int"),
                    ("bool", "bool"))))
        grid.allow_paging = False
        grid.store = ext.ExtDataStore()
        grid.store._id_property = "key"
        grid.editor = True
        grid.row_id_name = "key"
        grid.top_bar.items.extend((
            ext.ExtButton(
                text=_(u"Добавить"),
                icon_cls="add_item",
                handler="function() {addProtocolParamItem(\"%s\")}"
                        % grid.client_id),
            ext.ExtButton(
                text=_(u"Удалить"),
                icon_cls="delete_item",
                handler="function() {deleteProtocolParamItem(\"%s\")}"
                        % grid.client_id)
        ))
        grid.sm = ext.ExtGridRowSelModel()
        handler = (
            "function(store){onParamEditing(store, \"%s\")}"
            % json_field.client_id)
        grid.store._listeners.update({
            "update": handler,
            "add": handler,
            "remove": handler,
        })
        return grid


def container(*items, **params):
    cnt = ext.ExtContainer(**params)
    cnt.items.extend(items)
    return cnt
