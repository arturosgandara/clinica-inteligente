# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class MagentoProductAttributeValue(models.Model):
    _name = "magento.product.attribute.value"
    _order = 'id desc'
    _description = "Magento Product Attribute Value"

    @api.model
    def create(self, vals):
        vals = self.update_vals(vals)
        return super(MagentoProductAttributeValue, self).create(vals)

    @api.multi
    def write(self, vals):
        vals = self.update_vals(vals)
        return super(MagentoProductAttributeValue, self).write(vals)

    def update_vals(self, vals):
        ctx = dict(self._context or {})
        if 'magento' in ctx:
            instanceId = ctx.get('instance_id', False)
            erpId = vals.get('name')
            if instanceId:
                vals.update({
                    'instance_id' : instanceId,
                    'erp_id' : erpId,
                    })
            else:
                vals.update({
                    'erp_id' : erpId
                    })
        return vals

    name = fields.Many2one('product.attribute.value', string='Attribute Value')
    erp_id = fields.Integer(string='Odoo Attribute Value Id')
    mage_id = fields.Integer(string='Magento Attribute Value Id')
    instance_id = fields.Many2one(
        'magento.configure', string='Magento Instance')
    created_by = fields.Char(string='Created By', default="odoo", size=64)
    create_date = fields.Datetime(string='Created Date')
    write_date = fields.Datetime(string='Updated Date')
