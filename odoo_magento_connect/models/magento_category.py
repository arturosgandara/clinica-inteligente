# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models
from .res_partner import _unescape


class MagentoCategory(models.Model):
    _name = "magento.category"
    _order = 'id desc'
    _rec_name = "cat_name"
    _description = "Magento Category"

    cat_name = fields.Many2one('product.category', string='Category Name')
    oe_category_id = fields.Integer(string='Odoo Category Id')
    mag_category_id = fields.Integer(string='Magento Category Id')
    instance_id = fields.Many2one(
        'magento.configure', string='Magento Instance')
    need_sync = fields.Selection(
        [('Yes', 'Yes'), ('No', 'No')], string='Update Required', default="No")
    create_date = fields.Datetime(string='Created Date')
    write_date = fields.Datetime(string='Updated Date')
    created_by = fields.Char(string='Created By', default="odoo", size=64)

    @api.model
    def create(self, vals):
        ctx = dict(self._context or {})
        if ctx.get('instance_id'):
            vals['instance_id'] = ctx.get('instance_id')
        return super(MagentoCategory, self).create(vals)


    @api.model
    def create_category(self, data):
        """Create and update a category by any webservice like xmlrpc.
        @param data: details of category fields in list.
        """
        categDict = {}
        if data.get('name'):
            categDict['name'] = _unescape(data.get('name'))

        if data.get('type'):
            categDict['type'] = data.get('type')
        if data.get('parent_id'):
            categDict['parent_id'] = data.get('parent_id')
        if data.get('method') == 'create':
            mageCategoryId = data.get('mage_id')
            categoryObj = self.env['product.category'].create(categDict)
            odooMapVals = {
                'cat_name' : categoryObj.id,
                'oe_category_id' : categoryObj.id,
                'mag_category_id' : mageCategoryId,
                'instance_id' : self._context.get('instance_id'),
                'created_by' : 'Magento'
            }
            self.create(odooMapVals)
            return categoryObj.id
        if data.get('method') == 'write':
            categoryId = data.get('category_id')
            categoryObj = self.env['product.category'].browse(categoryId)
            categoryObj.write(categDict)
            return True
        return False
