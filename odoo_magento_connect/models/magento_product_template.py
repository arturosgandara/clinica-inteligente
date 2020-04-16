# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class MagentoProductTemplate(models.Model):
    _name = "magento.product.template"
    _order = 'id desc'
    _description = "Magento Product Template"

    @api.model
    def create(self, vals):
        ctx = dict(self._context or {})
        if 'magento' in ctx:
            vals['instance_id'] = ctx.get('instance_id')
            vals['erp_template_id'] = vals['template_name']
            if 'base_price' not in vals:
                vals['base_price'] = self.env['product.template'].browse(
                    vals['erp_template_id']).list_price
        return super(MagentoProductTemplate, self).create(vals)

    template_name = fields.Many2one('product.template', string='Template Name')
    erp_template_id = fields.Integer(string='Odoo`s Template Id')
    mage_product_id = fields.Integer(string='Magento`s Product Id')
    instance_id = fields.Many2one(
        'magento.configure', string='Magento Instance')
    base_price = fields.Float(string='Base Price(excl. impact)')
    is_variants = fields.Boolean(string='Is Variants')
    created_by = fields.Char(string='Created By', default="odoo", size=64)
    create_date = fields.Datetime(string='Created Date')
    write_date = fields.Datetime(string='Updated Date')
    need_sync = fields.Selection([
        ('Yes', 'Yes'),
        ('No', 'No')
    ], string='Update Required', default="No")

    @api.model
    def create_n_update_attribute_line(self, data):
        lineDict = {}
        prodAttrPriceModel = self.env['product.template.attribute.value']
        prodattrLineModel = self.env['product.template.attribute.line']
        if data.get('product_tmpl_id'):
            templateId = data.get('product_tmpl_id')
            attributeId = data.get('attribute_id')
            domain = [('product_tmpl_id', '=', templateId)]
            if data.get('values'):
                valueIds = []
                for value in data['values']:
                    valueId = value['value_id']
                    valueIds.append(valueId)
                    if value.get('price_extra'):
                        priceExtra = value['price_extra']
                        searchDomain = domain + [('product_attribute_value_id', '=', valueId)]
                        attrPriceObjs = prodAttrPriceModel.search(searchDomain)
                        if attrPriceObjs:
                            for attrPriceObj in attrPriceObjs:
                                attrPriceObj.write({'price_extra': priceExtra})
                        else:
                            attrPriceDict = {
                                'product_tmpl_id' : templateId,
                                'product_attribute_value_id' : valueId,
                                'price_extra' : priceExtra,
                            }
                            prodAttrPriceModel.create(attrPriceDict)
                lineDict['value_ids'] = [(6, 0, valueIds)]
            searchDomain = domain + [('attribute_id', '=', attributeId)]
            existAttrLineObjs = prodattrLineModel.search(searchDomain)
            if existAttrLineObjs:
                for existAttrLineObj in existAttrLineObjs:
                    existAttrLineObj.write(lineDict)
            else:
                lineDict.update({
                    'attribute_id' : attributeId,
                    'product_tmpl_id' : templateId
                })
                prodattrLineModel.create(lineDict)
            return True
        return False

    @api.model
    def create_template_mapping(self, data):
        ctx = dict(self._context or {})
        if data.get('erp_product_id'):
            templateObj = self.env['product.product'].browse(
                data.get('erp_product_id')).product_tmpl_id
            if not templateObj.attribute_line_ids :
                odooMapDict = {
                    'template_name' : templateObj.id,
                    'erp_template_id' : templateObj.id,
                    'mage_product_id' : data.get('mage_product_id'),
                    'instance_id' : ctx.get('instance_id'),
                    'created_by' : 'Manual Mapping'
                }
                res = self.create(odooMapDict)
        return True
