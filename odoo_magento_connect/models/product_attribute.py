# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################


from odoo import api, models


class ProductTemplateAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"

    @api.onchange('attribute_id')
    def onchange_attribute_id(self):
        result = {}
        setId = self._context.get('attribute_set_id')
        if setId:
            setObj = self.env["magento.attribute.set"].browse(setId)
            attributeIds = [x.id for x in setObj.attribute_ids]
            result['domain'] = {'attribute_id': [('id', 'in', attributeIds)]}
        return result

    @api.model
    def create(self, vals):
        if vals.get("product_tmpl_id") and not self._context.get('magento'):
            product_map_ids = self.env['magento.product.template'].search(
                [('template_name', '=', vals['product_tmpl_id'])])
            if product_map_ids:
                raise UserError(
                    "Error !! You can't introduce new attribute because this product is already synced at Magento. This error is coming because Magento never allow to add new attribute inside configurable products.")
        return super(ProductTemplateAttributeLine, self).create(vals)

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    @api.model
    def check_attribute(self, vals):
        if vals.get('name'):
            attributeObj = self.search(
                [('name', '=ilike', vals['name'])], limit=1)
            return attributeObj
        return False

    @api.model
    def create(self, vals):
        if 'magento' in self._context:
            attributeObj = self.check_attribute(vals)
            if attributeObj:
                return attributeObj
        return super(ProductAttribute, self).create(vals)


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    @api.model
    def create(self, vals):
        if 'magento' in self._context:
            attributeValueObjs = self.search([('name', '=', vals.get(
                'name')), ('attribute_id', '=', vals.get('attribute_id'))])
            if attributeValueObjs:
                return attributeValueObjs[0]
        return super(ProductAttributeValue, self).create(vals)
