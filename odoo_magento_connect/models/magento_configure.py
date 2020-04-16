# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import json
import re

import requests

from odoo import _, api, fields, models
from odoo.addons.base.models.res_partner import _lang_get
from odoo.exceptions import UserError
from odoo.http import request

XMLRPC_API = '/integration/admin/token'


class MagentoConfigure(models.Model):
    _name = "magento.configure"
    _inherit = ['mail.thread']
    _description = "Magento Configuration"
    _rec_name = 'instance_name'

    def _default_instance_name(self):
        return self.env[
            'ir.sequence'].next_by_code('magento.configure')

    def _default_category(self):
        ctx = dict(self._context or {})
        categId = ctx.get('categ_id', False)
        if categId:
            return categId
        try:
            return self.env['ir.model.data'].get_object_reference(
                'product', 'product_category_all')[1]
        except ValueError:
            return False

    def _fetch_magento_store(self, url, token):
        storeInfo = {}
        storeObj = self.env['magento.store.view']._get_store_view(url, token)
        storeInfo['store_id'] = storeObj
        return storeInfo

    name = fields.Char(
        string='Base URL',
        track_visibility="onchange",
        required=True,
    )
    instance_name = fields.Char(
        string='Instance Name',
        default=lambda self: self._default_instance_name())
    user = fields.Char(
        string='User Name',
        track_visibility="onchange",
        required=True)
    pwd = fields.Char(
        string='Password',
        track_visibility="onchange",
        required=True,
        size=100)
    token = fields.Char(string='Token', size=100)
    status = fields.Char(string='Connection Status', readonly=True)
    active = fields.Boolean(
        string="Active",
        track_visibility="onchange",
        default=True)
    connection_status = fields.Boolean(
        string="Connection Status", default=False)
    store_id = fields.Many2one(
        'magento.store.view', string='Default Magento Store')
    group_id = fields.Many2one(
        related="store_id.group_id",
        string="Default Store",
        readonly=True,
        store=True)
    website_id = fields.Many2one(
        related="group_id.website_id",
        string="Default Magento Website",
        readonly=True)
    credential = fields.Boolean(
        string="Show/Hide Credentials Tab",
        default=lambda *a: 1,
        help="If Enable, Credentials tab will be displayed, "
        "And after filling the details you can hide the Tab.")
    notify = fields.Boolean(
        string='Notify Customer By Email',
        default=lambda *a: 1,
        help="If True, customer will be notify"
        "during order shipment and invoice, else it won't.")
    language = fields.Selection(
        _lang_get, string="Default Language", default=api.model(
            lambda self: self.env.lang), help="Selected language is loaded in the system, "
        "all documents related to this contact will be synched in this language.")
    category = fields.Many2one(
        'product.category',
        string="Default Category",
        default=lambda self: self._default_category(),
        help="Selected Category will be set default category for odoo's product, "
        "in case when magento product doesn\'t belongs to any catgeory.")
    state = fields.Selection([
            ('enable','Enable'),
            ('disable','Disable')
        ],
        string='Status',
        default="enable",
        help="status will be consider during order invoice, "
        "order delivery and order cancel, to stop asynchronous process at other end.",
        size=100)
    inventory_sync = fields.Selection([
            ('enable','Enable'),
            ('disable','Disable')
        ],
        string='Inventory Update',
        default="enable",
        help="If Enable, Invetory will Forcely Update During Product Update Operation.",
        size=100)
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        default=lambda self: self.env['sale.order']._default_warehouse_id(),
        help="Used During Inventory Synchronization From Magento to Odoo.")
    location_id = fields.Many2one(
        related='warehouse_id.lot_stock_id', string='Location')
    create_date = fields.Datetime(string='Created Date')
    correct_mapping = fields.Boolean(string='Correct Mapping', default=True)

    @api.model
    def create(self, vals):
        activeConnections = self.search([('active', '=', True)])
        isMultiMobInstalled = False
        if self.env['ir.module.module'].sudo().search(
                [('name', 'in', ['odoo_magento_multi_instance', 'mob_hybrid_multi_instance'])], limit=1).state == 'installed':
            isMultiMobInstalled = True
        if vals.get('active') and activeConnections and not isMultiMobInstalled:
            raise UserError(
                _('Warning!\nSorry, Only one active connection is allowed.'))
        vals['instance_name'] = self.env[
            'ir.sequence'].next_by_code('magento.configure')
        res = super(MagentoConfigure, self).create(vals)
        self.env['mob.dashboard']._create_dashboard(res)
        return res

    @api.multi
    def write(self, vals):
        activeConnections = self.search([('active', '=', True)])
        isMultiMobInstalled = False
        dashboardModel = self.env['mob.dashboard']
        if self.env['ir.module.module'].sudo().search(
                [('name', 'in', ['odoo_magento_multi_instance', 'mob_hybrid_multi_instance'])], limit=1).state == 'installed':
            isMultiMobInstalled = True
        if vals:
            if len(activeConnections) > 0 and vals.get(
                    'active') and not isMultiMobInstalled:
                raise UserError(
                    _('Warning!\nSorry, Only one active connection is allowed.'))
            for instanceObj in self:
                if (vals.get('name') and vals['name'] != instanceObj.name) or \
                    (vals.get('user') and vals['user'] != instanceObj.user) or \
                    (vals.get('pwd') and vals['pwd'] != instanceObj.pwd):
                    token = instanceObj.create_magento_connection(vals)
                    if token:
                        if len(token[0]) > 1:
                            if token[0][0]:
                                vals['token'] = str(token[0][0])
                                vals[
                                    'status'] = "Congratulation, It's Successfully Connected with Magento Api."
                                vals['connection_status'] = True
                            else:
                                vals['token'] = False
                                vals['status'] = str(token[0][1])
                                vals['connection_status'] = False
                if not instanceObj.instance_name:
                    vals['instance_name'] = self.env[
                        'ir.sequence'].next_by_code('magento.configure')
                isDashboardExist = dashboardModel.with_context(
                    active_test=False).search([('instance_id', '=', self.id)])
                if not isDashboardExist:
                    dashboardModel._create_dashboard(instanceObj)
        return super(MagentoConfigure, self).write(vals)

    @api.multi
    def set_default_magento_website(self, url, token):
        for obj in self:
            storeId = obj.store_id
            ctx = dict(self._context or {})
            ctx['instance_id'] = obj.id
            if not storeId:
                storeInfo = self.with_context(
                    ctx)._fetch_magento_store(url, token)
                if not storeInfo:
                    raise UserError(
                        _('Error!\nMagento Default Website Not Found!!!'))
        return True

    #############################################
    ##          magento connection             ##
    #############################################
    @api.multi
    def test_connection(self):
        token = 0
        connectionStatus = False
        status = 'Magento Connection Un-successful'
        text = 'Test connection Un-successful please check the magento login credentials !!!'
        checkMapping = self.correct_mapping
        token = self.create_magento_connection()
        if token:
            if len(token[0]) > 1:
                if token[0][0]:
                    self.token = str(token[0][0])
                    storeId = self.set_default_magento_website(
                        self.name, self.token)
                    text = str(token[0][1])
                    status = "Congratulation, It's Successfully Connected with Magento."
                    connectionStatus = True
                else:
                    status = str(token[0][1])
        self.status = status
        res_model = 'message.wizard'
        partial = self.env['message.wizard'].create({'text': text})
        view_id = self.env.ref('odoo_magento_connect.message_wizard_form1').id
        if not self.store_id and connectionStatus:
            partial = self.env['magento.wizard'].create(
                {'magento_store_view': self.store_id.id})
            view_id = self.env.ref(
                'odoo_magento_connect.id_magento_wizard_form').id
            res_model = 'magento.wizard'
        if checkMapping:
            self.correct_instance_mapping()
        ctx = dict(self._context or {})
        ctx['text'] = text
        ctx['instance_id'] = self.id
        self.connection_status = connectionStatus
        return {'name': ("Odoo Magento Bridge"),
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': res_model,
                'view_id': view_id,
                'res_id': partial.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'context': ctx,
                'target': 'new',
                }

    @api.model
    def _create_connection(self):
        """ create a connection between Odoo and magento 
                returns: False or list"""
        instanceId = self._context.get('instance_id', False)
        token = ''
        if instanceId:
            instanceObj = self.browse(instanceId)
        else:
            activeConnections = self.search([('active', '=', True)])
            if len(activeConnections) > 1:
                raise UserError(
                    _('Error!\nSorry, only one Active Configuration setting is allowed.'))
            if not activeConnections:
                raise UserError(
                    _('Error!\nPlease create the configuration part for Magento connection!!!'))
            else:
                instanceObj = activeConnections[0]
        token_generation = instanceObj.create_magento_connection()
        if token_generation:
            if len(token_generation[0]) > 1:
                if token_generation[0][0]:
                    instanceObj.token = token_generation[0][0]
                    token = token_generation[0][0]
        if token:
            return [instanceObj.name, token, instanceObj.id]
        else:
            return False

    @api.one
    def create_magento_connection(self, vals={}):
        text, token = '', ''
        url = self.name + "/index.php/rest/V1" + XMLRPC_API
        user = self.user
        pwd = self.pwd
        if vals:
            if vals.get('name'):
                url = vals['name'] + "/index.php/rest/V1" + XMLRPC_API
            if vals.get('user'):
                user = vals['user']
            if vals.get('pwd'):
                pwd = vals['pwd']
        Cre = {
            "username": user,
            "password": pwd
        }
        Cred = json.dumps(Cre)
        userAgent = request.httprequest.environ.get('HTTP_USER_AGENT', '')
        headers = {'Content-Type': 'application/json', 'User-Agent': userAgent, 'User-Agent': userAgent}
        try:
            responseApi = requests.post(url, data=Cred, headers=headers, verify=False)
            response = json.loads(responseApi.text)
            if responseApi.ok :
                token = "Bearer " + response
                text = 'Test Connection with magento is successful, now you can proceed with synchronization.'
            else :
                text = ('Magento Connection Error: %s') % response.get('message')
        except Exception as e:
            text = ('Error!\nMagento Connection Error: %s') % e
        return [token, text]

    @api.model
    def fetch_connection_info(self, vals):
        """
                Called by Xmlrpc from Magento
        """
        if vals.get('magento_url'):
            activeConnections = self.search([('active', '=', True)])
            isMultiMobInstalled = self.env['ir.module.module'].sudo().search(
                [('name', 'in', ['odoo_magento_multi_instance', 'mob_hybrid_multi_instance']), ("state", "=", "installed")])
            if isMultiMobInstalled:
                magentoUrl = re.sub(r'^https?:\/\/', '', vals.get('magento_url'))
                magentoUrl = re.split('index.php', magentoUrl)[0]
                for connectionObj in activeConnections:
                    act = connectionObj.name
                    act = re.sub(r'^https?:\/\/', '', act)
                    if magentoUrl == act or magentoUrl[:-1] == act:
                        return connectionObj.read(
                            ['language', 'category', 'warehouse_id'])[0]
            else:
                for connectionObj in activeConnections:
                    return connectionObj.read(
                        ['language', 'category', 'warehouse_id'])[0]
        return False

    @api.model
    def correct_instance_mapping(self):
        self.mapped_status("magento.product")
        self.mapped_status("magento.product.template")
        self.mapped_status("wk.order.mapping")
        self.mapped_status("magento.customers")
        self.mapped_status("magento.product.attribute.value")
        self.mapped_status("magento.product.attribute")
        self.mapped_status("magento.category")
        self.mapped_status("magento.website")
        self.mapped_status("magento.store")
        self.mapped_status("magento.store.view")
        self.mapped_status("magento.attribute.set")
        return True

    @api.model
    def mapped_status(self, model):
        falseInstances = self.env[model].search([('instance_id', '=', False)])
        if falseInstances:
            falseInstances.write({'instance_id': self.id})
        return True
    
    @api.model
    def mob_upgrade_hook(self):
        activeConfigs = self.sudo().search([('active', '=', True)])
        for activeConfig in activeConfigs :
            activeConfig.sudo().test_connection()

    @api.model
    def _mob_def_setting(self):
        configModel = self.env['res.config.settings']
        vals = {
            'mob_sale_order_invoice' : True,
            'mob_sale_order_shipment' : True,
            'mob_sale_order_cancel' : True,
            }
        defaultSetObj = configModel.create(vals)
        defaultSetObj.execute()
        return True
