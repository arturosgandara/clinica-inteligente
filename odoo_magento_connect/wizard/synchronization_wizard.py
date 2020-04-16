# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class SynchronizationWizard(models.TransientModel):
    _name = 'synchronization.wizard'

    action = fields.Selection([('export', 'Export'), ('update', 'Update')], string='Action', default="export", required=True,
                              help="""Export: Export all Odoo Category/Products at Magento. Update: Update all synced products/categories at magento, which requires to be update at magento""")

    @api.multi
    def start_category_synchronization(self):
        ctx = dict(self._context or {})
        ctx['sync_opr'] = self.action
        message = self.env['magento.synchronization'].with_context(
            ctx).export_categories_check()
        return message

    @api.multi
    def start_category_synchronization_mapping(self):
        ctx = dict(self._context or {})
        mappedIds = ctx.get('active_ids')
        mpaObjs = self.env['magento.category'].browse(mappedIds)
        mapCategIds = mpaObjs.mapped('cat_name').ids
        ctx.update(
            sync_opr=self.action,
            active_model='product.category',
            active_ids=mapCategIds,
        )
        message = self.env['magento.synchronization'].with_context(
            ctx).export_categories_check()
        return message

    @api.multi
    def start_bulk_category_synchronization_mapping(self):
        partial = self.create({'action': 'update'})
        ctx = dict(self._context or {})
        ctx['mapping_categ'] = False
        return {'name': "Synchronization Bulk Category",
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'synchronization.wizard',
                'res_id': partial.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'context': ctx,
                'domain': '[]',
                }

    @api.multi
    def start_product_synchronization(self):
        ctx = dict(self._context or {})
        ctx['sync_opr'] = self.action
        message = self.env['magento.synchronization'].with_context(
            ctx).export_product_check()
        return message

    @api.multi
    def start_product_synchronization_mapping(self):
        ctx = dict(self._context or {})
        mappedIds = ctx.get('active_ids')
        mpaObjs = self.env['magento.product.template'].browse(mappedIds)
        maptemplateIds = mpaObjs.mapped('template_name').ids
        ctx.update(
            sync_opr=self.action,
            active_model='product.template',
            active_ids=maptemplateIds,
        )
        message = self.env['magento.synchronization'].with_context(
            ctx).export_product_check()
        return message

    @api.multi
    def start_bulk_product_synchronization_mapping(self):
        partial = self.create({'action': 'update'})
        ctx = dict(self._context or {})
        ctx['mapping'] = False
        return {'name': "Synchronization Bulk Product",
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'synchronization.wizard',
                'res_id': partial.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'context': ctx,
                'domain': '[]',
                }

    @api.model
    def start_bulk_product_synchronization(self):
        partial = self.create({})
        ctx = dict(self._context or {})
        ctx['check'] = False
        return {'name': "Synchronization Bulk Product",
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'synchronization.wizard',
                'res_id': partial.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'context': ctx,
                'domain': '[]',
                }

    @api.model
    def start_bulk_category_synchronization(self):
        partial = self.create({})
        ctx = dict(self._context or {})
        ctx['All'] = True
        return {'name': "Synchronization Bulk Category",
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'synchronization.wizard',
                'res_id': partial.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'context': ctx,
                'domain': '[]',
                }
