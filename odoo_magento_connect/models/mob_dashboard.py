# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import json
import logging
import datetime
from dateutil.relativedelta import relativedelta
from datetime import timedelta

from babel.dates import format_date, format_datetime

from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.release import version
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

Item_Type = [
    ('product', 'Product'),
    ('order', 'Order'),
    ('attribute', 'Attribute'),
    ('category', 'Category'),
    ('partner', 'Partner'),
]

modelName = {
    'product': [
        1,
        'product.template',
        'magento.product.template',
        'template_name',
        'magento_product_template'],
    'category': [
        1,
        'product.category',
        'magento.category',
        'cat_name',
        'magento_category'],
    'order': [
        2,
        'sale.order',
        'wk.order.mapping',
        'erp_order_id',
        'wk_order_mapping'],
    'partner': [
        0,
        'res.partner',
        'magento.customers',
        '',
        'magento_customers'],
    'attribute': [
        0,
        'product.attribute',
        'magento.product.attribute',
        'name',
        'magento_product_attribute'],
}

fieldName = {
    'product': [
        'count_need_sync_product',
        'count_no_sync_product',
        'product.product_template_form_view'],
    'category': [
        'count_need_sync_category',
        'count_no_sync_category',
        'product.product_category_form_view'],
    'order': [
        'count_need_invoice',
        'count_need_delivery',
        'sale.view_order_form'],
    'partner': [
        '',
        '',
        'base.view_partner_form'],
    'attribute': [
        '',
        'count_no_sync_attribute',
        'product.product_attribute_view_form'],
}


class MobDashboard(models.Model):
    _name = "mob.dashboard"
    _description = "MOB Dashboard"

    @api.one
    def _kanban_dashboard_graph(self):
        self.kanban_dashboard_graph = json.dumps(
            self.get_bar_graph_datas(self.item_name))

    name = fields.Char(string="Dashboard Item")
    instance_id = fields.Many2one(
        'magento.configure', 'Magento Instance', ondelete='cascade',
        default=lambda self: self.env['magento.configure'].search([('active', '=', True)], limit=1))
    active = fields.Boolean(related="instance_id.active")
    item_name = fields.Selection(
        Item_Type, string="Dashboard Item Name")
    color = fields.Integer(string='Color Index')
    kanban_dashboard_graph = fields.Text(compute='_kanban_dashboard_graph')
    count_mapped_records = fields.Integer(compute='_compute_record_count')
    count_need_sync_product = fields.Integer(compute='_compute_record_count')
    count_no_sync_product = fields.Integer(compute='_compute_record_count')
    count_need_sync_category = fields.Integer(compute='_compute_record_count')
    count_no_sync_category = fields.Integer(compute='_compute_record_count')
    count_need_invoice = fields.Integer(compute='_compute_record_count')
    count_need_delivery = fields.Integer(compute='_compute_record_count')
    count_invoiced_records = fields.Integer(compute='_compute_record_count')
    count_delivered_records = fields.Integer(compute='_compute_record_count')
    count_no_sync_attribute = fields.Integer(compute='_compute_record_count')

    @api.model
    def get_connection_info(self):
        configModel = self.env['magento.configure']
        success = False
        defId = False
        activeConObjs = configModel.search([('active', '=', True)])
        inactiveConObjs = configModel.search([('active', '=', False)])
        if activeConObjs:
            defConnection = activeConObjs[0]
            defId = defConnection.id
            if defConnection.connection_status:
                success = True
        totalConnections = activeConObjs.ids + inactiveConObjs.ids
        res = {
            'totalcon' : len(totalConnections),
            'total_ids' : totalConnections,
            'active_ids' : activeConObjs.ids,
            'inactive_ids' : inactiveConObjs.ids,
            'active' : len(activeConObjs.ids),
            'inactive' : len(inactiveConObjs.ids),
            'def_id' : defId,
            'success' : success
        }
        return res

    @api.multi
    def open_configuration(self):
        self.ensure_one()
        instanceId = self.instance_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configure Magento Api',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'magento.configure',
            'res_id': instanceId,
            'target': 'current',
            'domain': '[]',
        }

    @api.model
    def _create_dashboard(self, instanceObj):
        for itemName in Item_Type:
            vals = {
                'name' : itemName[1],
                'instance_id' : instanceObj.id,
                'item_name' : itemName[0],
            }
            self.create(vals)
        return True

    @api.multi
    def _compute_record_count(self):
        for singleRecord in self:
            instanceId = singleRecord.instance_id.id
            name = singleRecord.item_name
            needOne = fieldName[name][0]
            needTwo = fieldName[name][1]
            model = modelName[name][1]
            mappedModel = modelName[name][2]
            mappedfieldName = modelName[name][3]
            action = modelName[name][0]
            if action == 1:
                totalOne = self._get_need_sync_record(mappedModel, instanceId)
                totalTwo = self._get_no_sync_record(
                    model, mappedModel, mappedfieldName, instanceId)
                singleRecord[needOne] = totalOne
                singleRecord[needTwo] = totalTwo
            elif action == 2:
                totalInvc, totalNeedInv, totalDlvr, totlaNeedDlvr = self._get_processed_unprocessed_records(
                    instanceId)
                singleRecord[needOne] = len(totalNeedInv)
                singleRecord[needTwo] = len(totlaNeedDlvr)
                singleRecord.count_invoiced_records = len(totalInvc)
                singleRecord.count_delivered_records = len(totalDlvr)
            elif mappedfieldName:
                singleRecord[needTwo] = self._get_no_sync_record(
                    model, mappedModel, mappedfieldName, instanceId)
            singleRecord.count_mapped_records = self._get_mapped_records(
                mappedModel, instanceId)

    @api.model
    def _get_mapped_records(self, mappedModel, instanceId):
        return len(self.env[mappedModel].search(
            [('instance_id', '=', instanceId)]))

    @api.model
    def _get_need_so_action_record(self, instanceId, needAction):
        recordMapObjs = self.env['wk.order.mapping'].search(
            [('instance_id', '=', instanceId)])
        saleOrderObjs = recordMapObjs.mapped('erp_order_id')
        idList = []
        for orderObj in saleOrderObjs.filtered(
                lambda obj: obj.state != 'cancel'):
            if needAction == 'delivery':
                if not orderObj.is_shipped:
                    idList.append(orderObj.id)
            if needAction == 'invoice':
                if not orderObj.is_invoiced:
                    idList.append(orderObj.id)

        return idList

    @api.model
    def _get_process_order_record(self, instanceId, doneAction):
        recordMapObjs = self.env['wk.order.mapping'].search(
            [('instance_id', '=', instanceId)])
        recList = []
        for orderObj in recordMapObjs:
            if doneAction == 'invoice' and orderObj.is_invoiced:
                recList.append(orderObj.erp_order_id.id)
            if doneAction == 'delivery' and orderObj.is_shipped:
                recList.append(orderObj.erp_order_id.id)
        return recList

    @api.model
    def _get_processed_unprocessed_records(self, instanceId):
        recordMapObjs = self.env['wk.order.mapping'].search(
            [('instance_id', '=', instanceId)])
        saleOrderIds = recordMapObjs.mapped('erp_order_id').ids
        filterDate = self.get_order_fitler_date()
        domain = [
            ('id', 'in', saleOrderIds),
            ('state', '!=', 'cancel'),
            ('confirmation_date', '>=', filterDate)]
        saleOrderObjs = self.env['sale.order'].search(domain)
        totalInvc, totalNeedInv, totalDlvr, totlaNeedDlvr = [], [], [], []
        for orderObj in saleOrderObjs:
            if orderObj.is_invoiced:
                totalInvc.append(orderObj.id)
            else:
                totalNeedInv.append(orderObj.id)
            if orderObj.is_shipped:
                totalDlvr.append(orderObj.id)
            else:
                totlaNeedDlvr.append(orderObj.id)
        return [totalInvc, totalNeedInv, totalDlvr, totlaNeedDlvr]


    @api.model
    def get_order_fitler_date(self):
        crntDate = datetime.datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        dateFormat = '%Y-%m-%d %H:%M:%S'
        crntDate = datetime.datetime.strptime(crntDate, dateFormat)
        filterDate = crntDate + relativedelta(days=-30)
        return filterDate

    @api.multi
    def get_action_prosess_records(self):
        self.ensure_one()
        instanceId = self.instance_id.id
        doneAction = self._context.get('action')
        doneActionIds = self._get_process_order_record(instanceId, doneAction)
        return {
            'name': ('Records'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'domain': [('id', 'in', doneActionIds)],
            'target': 'current',
        }

    @api.multi
    def action_open_order_need(self):
        self.ensure_one()
        instanceId = self.instance_id.id
        needAction = self._context.get('action')
        neddActionIds = self._get_need_so_action_record(instanceId, needAction)
        return {
            'name': ('Record'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'domain': [('id', 'in', neddActionIds)],
            'target': 'current',
        }

    @api.model
    def _get_need_sync_record(self, mappedModel, instanceId):
        domain = [('need_sync', '=', "Yes"), ('instance_id', '=', instanceId)]
        needSyncObjs = self.env[mappedModel].search(domain)
        return len(needSyncObjs)

    @api.model
    def _get_no_sync_record(
            self,
            model,
            mappedModel,
            mappedfieldName,
            instanceId):
        if model == "product.template":
            domin = [('type', '!=', 'service')]
        else:
            domin = []
        allRecordIds = self.env[model].search(domin).ids
        allSyncedObjs = self.env[mappedModel].search(
            [('instance_id', '=', instanceId)])
        allSynedRecordIds = allSyncedObjs.mapped(mappedfieldName).ids
        return len(set(allRecordIds) - set(allSynedRecordIds))

    @api.multi
    def get_action_mapped_records(self):
        self.ensure_one()
        resModel = self._context.get('map_model')
        recordIds = self.env[resModel].search(
            [('instance_id', '=', self.instance_id.id)]).ids
        return {
            'name': ('Records'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': resModel,
            'view_id': False,
            'domain': [('id', 'in', recordIds)],
            'target': 'current',
        }

    @api.multi
    def open_action(self):
        self.ensure_one()
        itemType = self.item_name
        ctx = dict(
            map_model=modelName[itemType][2]
        )
        res = self.with_context(ctx).get_action_mapped_records()
        return res

    @api.multi
    def show_report(self):
        self.ensure_one()
        ctx = dict(self._context or {})
        repType = ctx.get('r_type')
        itemType = self.item_name
        if itemType == "partner":
            itemType = "customer"
        if repType == 'success':
            status = 'yes'
        else:
            status = 'no'
        resModel = "magento.sync.history"
        domain = [('status', '=', status), ('action_on', '=', itemType)]
        itemHistory = self.env[resModel].search(domain).ids
        return {
            'name': ('Reports'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': resModel,
            'view_id': False,
            'domain': [('id', 'in', itemHistory)],
            'target': 'current',
        }

    @api.multi
    def open_view_rec(self):
        self.ensure_one()
        ctx = dict(self._context or {})
        instanceId = self.instance_id.id
        resModel = ctx.get('res_model')
        rType = ctx.get('rec_type')
        domain = [('instance_id', '=', instanceId)]
        if rType == 'config':
            domain += [('is_variants', '=', True)]
        elif rType == 'simple':
            domain += [('is_variants', '=', False)]
        elif rType == 'partner':
            domain += [('mag_address_id', '=', 'customer')]
        elif rType == 'address':
            domain += [('mag_address_id', '!=', 'customer')]
        recIds = self.env[resModel].search(domain).ids
        return {
            'name': ('Records'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': resModel,
            'view_id': False,
            'domain': [('id', 'in', recIds)],
            'target': 'current',
        }

    @api.multi
    def open_order_view_rec(self):
        self.ensure_one()
        ctx = dict(self._context or {})
        instanceId = self.instance_id.id
        resModel = ctx.get('res_model')
        rType = ctx.get('rec_type')
        domain = [('instance_id', '=', instanceId)]
        orderObjs = self.env[resModel].search(domain)
        recIds = []
        for orderObj in orderObjs:
            if orderObj.order_status == rType:
                recIds.append(orderObj.id)

        return {
            'name': ('Records'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': resModel,
            'view_id': False,
            'domain': [('id', 'in', recIds)],
            'target': 'current',
        }

    @api.multi
    def action_open_update_records(self):
        self.ensure_one()
        resModel = self._context.get('map_model')
        domain = [('instance_id', '=', self.instance_id.id),
                  ('need_sync', '=', 'Yes')]
        recordIds = self.env[resModel].search(domain).ids
        return {
            'name': ('Record'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': resModel,
            'view_id': False,
            'domain': [('id', 'in', recordIds)],
            'target': 'current',
        }

    @api.multi
    def create_new_rec(self):
        self.ensure_one()
        ctx = dict(self._context or {})
        itemType = self.item_name
        resModel = modelName[itemType][1]
        envRefId = fieldName[itemType][2]
        viewId = self.env.ref(envRefId).id
        return {
            'name': _('Create invoice/bill'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': resModel,
            'view_id': viewId,
            'context': ctx,
        }

    @api.multi
    def action_open_export_records(self):
        self.ensure_one()
        mapModel = self._context.get('map_model')
        coreModel = self._context.get('core_model')
        fieldName = self._context.get('field_name')
        domain = []
        mappedObj = self.env[mapModel].search(
            [('instance_id', '=', self.instance_id.id)])
        mapObjIds = mappedObj.mapped(fieldName).ids
        if coreModel == 'product.template':
            domain += [('type', '!=', 'service')]
        recordIds = self.env[coreModel].search(domain).ids
        notMapIds = list(set(recordIds) - set(mapObjIds))

        return {
            'name': ('Record'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': coreModel,
            'view_id': False,
            'domain': [('id', 'in', notMapIds)],
            'target': 'current',
        }

    @api.multi
    def get_bar_graph_datas(self, itemName):
        self.ensure_one()
        itemType = self.item_name
        if itemType in ['order', 'partner']:
            fecthDate = 'create_date'
        else:
            fecthDate = 'write_date'
        moduleDB = modelName[itemType][4]
        data = []
        today = fields.Date.context_today(self)
        data.append({'label': _('Past'), 'value': 0.0})
        day_of_week = int(
            format_datetime(
                today,
                'e',
                locale=self._context.get(
                    'lang',
                    'en_US')))
        first_day_of_week = today + timedelta(days=-day_of_week + 1)
        for i in range(-1, 1):
            if i == 0:
                label = _('This Week')
            else:
                start_week = first_day_of_week + timedelta(days=i * 7)
                end_week = start_week + timedelta(days=6)
                if start_week.month == end_week.month:
                    label = str(start_week.day) + '-' + str(end_week.day) + ' ' + format_date(
                        end_week, 'MMM', locale=self._context.get('lang', 'en_US'))
                else:
                    label = format_date(start_week,
                                        'd MMM',
                                        locale=self._context.get('lang',
                                                                 'en_US')) + '-' + format_date(end_week,
                                                                                               'd MMM',
                                                                                               locale=self._context.get('lang',
                                                                                                                        'en_US'))
            data.append({'label': label, 'value': 0.0})

        # Build SQL query to find amount aggregated by week
        select_sql_clause = """SELECT COUNT(*) as total FROM """ + \
            moduleDB + """ where instance_id = %(instance_id)s """
        query = ''
        start_date = (first_day_of_week + timedelta(days=-7))
        for i in range(0, 3):
            if i == 0:
                query += "(" + select_sql_clause + " and " + \
                    fecthDate + " < '" + start_date.strftime(DF) + "')"
            else:
                next_date = start_date + timedelta(days=7)
                query += " UNION ALL (" + select_sql_clause + " and " + fecthDate + " >= '" + start_date.strftime(
                    DF) + "' and " + fecthDate + " < '" + next_date.strftime(DF) + "')"
                start_date = next_date

        self.env.cr.execute(query, {'instance_id': self.instance_id.id})
        query_results = self.env.cr.dictfetchall()
        for index in range(0, len(query_results)):
            total = str(query_results[index].get('total'))
            total = total.split('L')
            if int(total[0]) > 0:
                data[index]['value'] = total[0]

        color = '#7c7bad'
        graphData = [{'values': data, 'area': True, 'title': '', 'key': itemName.title(), 'color': color}]
        return graphData



    @api.model
    def dashboard_extend_data(self):
        pass

    @api.model
    def open_bulk_synchronization(self):
        viewId = self.env.ref(
            'odoo_magento_connect.magento_synchronization_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Magento Synchronization'),
            'res_model': 'magento.synchronization',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [[viewId, 'form']],
        }

    @api.model
    def create_new_connection(self):
        action = self.env.ref(
            'odoo_magento_connect.magento_configure_tree_action').read()[0]
        action['views'] = [
            (self.env.ref('odoo_magento_connect.magento_configure_form').id, 'form')]
        return action

    @api.model
    def open_mob_success_connection(self):
        connInfo = self.get_total_connection()
        # if connInfo[0] == 1 and connInfo[1]:
        #     return self.open_connection_form(connInfo[1])
        sccssCOn = connInfo[1].filtered(
            lambda obj: obj.connection_status == True)
        return self.open_connection_form(sccssCOn[0])
        # return self.open_connection_tree(connInfo[1], 'search_default_success')

    @api.model
    def open_mob_error_connection(self):
        connInfo = self.get_total_connection()
        errorCOn = connInfo[1].filtered(
            lambda obj: obj.connection_status == False)
        # if connInfo[0] == 1 and connInfo[1]:
        #     return self.open_connection_form(connInfo[1])
        return self.open_connection_form(errorCOn[0])
        # return self.open_connection_tree(connInfo[1], 'search_default_error')

    @api.model
    def get_total_connection(self):
        totalActiveConn = self.env['magento.configure'].search(
            [('active', '=', True)])
        if totalActiveConn and len(totalActiveConn) == 1:
            return [1, totalActiveConn]
        return [2, totalActiveConn]

    @api.model
    def open_connection_form(self, connObj):
        action = self.env.ref(
            'odoo_magento_connect.magento_configure_tree_action').read()[0]
        action['views'] = [
            (self.env.ref('odoo_magento_connect.magento_configure_form').id, 'form')]
        action['res_id'] = connObj.id
        return action