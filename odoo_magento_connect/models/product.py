# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import binascii

import requests

from odoo import _, api, fields, models
from .res_partner import _unescape


class ProductProduct(models.Model):
    _inherit = 'product.product'

    mob_mapping_ids = fields.One2many(
        string='Mappings',
        comodel_name='magento.product',
        inverse_name='pro_name',
        copy=False
    )


    @api.model
    def create(self, vals):
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        mapTempModel = self.env['magento.product.template']
        if 'magento' in ctx:
            mageId = vals.pop('mage_id', 0)
            magento_stock_id = vals.pop('magento_stock_id', 0)
            attrValIds = vals.get('value_ids', [])
            vals = self.update_vals(vals, instanceId, True)
        productObj = super(ProductProduct, self).create(vals)
        if 'magento' in ctx:
            attrValModel = self.env['product.attribute.value']
            attrLineModel = self.env['product.template.attribute.line']
            templateId = productObj.product_tmpl_id.id
            if templateId:
                mappDict = {
                    'instance_id' : instanceId,
                    'created_by' : 'Magento',
                }
                domain = [('product_tmpl_id', '=', templateId)]
                for attrValId in attrValIds:
                    attrId = attrValModel.browse(attrValId).attribute_id.id
                    searchDomain = domain + [('attribute_id', '=', attrId)]
                    attrLineObjs = attrLineModel.search(searchDomain)
                    for attrLineObj in attrLineObjs:
                        attrLineObj.value_ids = [(4, attrValId)]
                if mageId:
                    mapTempObjs = mapTempModel.search([
                        ('erp_template_id', '=', templateId), 
                        ('instance_id', '=', instanceId)
                    ])
                    if not mapTempObjs:
                        price = vals.get('list_price', 0)
                        mapTempDict = mappDict.copy()
                        mapTempDict.update({
                            'template_name' : templateId,
                            'erp_template_id' : templateId,
                            'mage_product_id' : mageId,
                            'base_price' : price,
                        })
                        mapTempModel.create(mapTempDict)
                    else:
                        mapTempObjs.need_sync = 'No'
                    mappDict.update({
                        'pro_name' : productObj.id,
                        'oe_product_id' : productObj.id,
                        'mag_product_id' : mageId,
                        'magento_stock_id' : magento_stock_id
                    })
                    self.env['magento.product'].create(mappDict)

        return productObj

    @api.multi
    def write(self, vals):
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id', False)
        mapProdModel = self.env['magento.product']
        mapTempModel = self.env['magento.product.template']
        if 'magento' in ctx:
            vals.pop('mage_id', None)
            vals.pop('magento_stock_id', None)
            vals = self.update_vals(vals, instanceId)
        for prodObj in self:
            mapObjs, tempMapObjs = [], []
            mapObjs = mapProdModel.search([('pro_name', '=', prodObj.id)])
            for mappedObj in mapObjs:
                if instanceId and mappedObj.instance_id.id == instanceId:
                    mappedObj.need_sync = "No"
                else:
                    mappedObj.need_sync = "Yes"
            templateId = prodObj.product_tmpl_id.id
            tempMapObjs = mapTempModel.search(
                [('template_name', '=', templateId)])
            for tempMapObj in tempMapObjs:
                if instanceId and tempMapObj.instance_id.id == instanceId:
                    tempMapObj.need_sync = "No"
                else:
                    tempMapObj.need_sync = "Yes"
        return super(ProductProduct, self).write(vals)

    def update_vals(self, vals, instanceId, create=False):
        if vals.get('default_code'):
            vals['default_code'] = _unescape(vals['default_code'])
        category_ids = vals.pop('category_ids', None)
        if category_ids:
            categIds = list(set(category_ids))
            defaultCategObj = self.env["magento.configure"].browse(
                instanceId).category
            if defaultCategObj and create:
                vals['categ_id'] = defaultCategObj.id
            vals['categ_ids'] = [(6, 0, categIds)]
        attrValIds = vals.pop('value_ids', [])
        if attrValIds:
            vals['attribute_value_ids'] = [(6, 0, attrValIds)]
        imageUrl = vals.pop('image_url', False)
        if imageUrl:
            proImage = binascii.b2a_base64(requests.get(imageUrl).content)
            vals['image'] = proImage
            vals['image_variant'] = proImage
        return vals


class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.multi
    def write(self, vals):
        if 'magento' in self._context:
            if vals.get('name'):
                vals['name'] = _unescape(vals['name'])
        else:
            categModel = self.env['magento.category']
            for catObj in self:
                mapObjs = categModel.search(
                    [('oe_category_id', '=', catObj.id)])
                for mapObj in mapObjs:
                    mapObjs.need_sync = "Yes"
        return super(ProductCategory, self).write(vals)
