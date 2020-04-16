# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class MagentoProductAttribute(models.Model):
    _name = "magento.product.attribute"
    _order = 'id desc'
    _description = "Magento Product Attribute"

    @api.model
    def create(self, vals):
        vals = self.update_vals(vals)
        return super(MagentoProductAttribute, self).create(vals)

    @api.multi
    def write(self, vals):
        vals = self.update_vals(vals)
        return super(MagentoProductAttribute, self).write(vals)

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

    name = fields.Many2one('product.attribute', string='Product Attribute')
    erp_id = fields.Integer(string='Odoo`s Attribute Id')
    mage_id = fields.Integer(string='Magento`s Attribute Id')
    mage_attribute_code = fields.Char(string="Magento`s Attribute Code")
    instance_id = fields.Many2one(
        'magento.configure', string='Magento Instance')
    created_by = fields.Char(string='Created By', default="odoo", size=64)
    create_date = fields.Datetime(string='Created Date')
    write_date = fields.Datetime(string='Updated Date')
