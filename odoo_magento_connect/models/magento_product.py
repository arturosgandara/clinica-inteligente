# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class MagentoProduct(models.Model):
    _name = "magento.product"
    _order = 'id desc'
    _rec_name = "pro_name"
    _description = "Magento Product"

    pro_name = fields.Many2one('product.product', string='Product Name')
    oe_product_id = fields.Integer(string='Odoo Product Id')
    mag_product_id = fields.Integer(string='Magento Product Id')
    magento_stock_id = fields.Integer(string='Magento Stock Item Id')
    need_sync = fields.Selection([
        ('Yes', 'Yes'),
        ('No', 'No')
    ], string='Update Required', default='No')
    instance_id = fields.Many2one(
        'magento.configure', string='Magento Instance')
    create_date = fields.Datetime(string='Created Date')
    write_date = fields.Datetime(string='Updated Date')
    created_by = fields.Char(string='Created By', default='odoo', size=64)

    @api.model
    def create(self, vals):
        ctx = dict(self._context or {})
        if ctx.get('instance_id'):
            vals['instance_id'] = ctx.get('instance_id')
        return super(MagentoProduct, self).create(vals)
