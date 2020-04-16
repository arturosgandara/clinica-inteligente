# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import codecs
import io
from urllib.parse import quote

from PIL import Image

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MagentoSynchronization(models.TransientModel):
    _inherit = "magento.synchronization"

    @api.model
    def get_sync_template_ids(self, templateIds):
        ctx = dict(self._context or {})
        mappedObj = self.env['magento.product.template'].search(
            [('instance_id', '=', ctx.get('instance_id'))])
        if ctx.get('sync_opr') == 'export':
            mapTemplateIds = mappedObj.mapped('template_name').ids
            notMappedTempltIds = list(set(templateIds) - set(mapTemplateIds))
            return notMappedTempltIds
        if ctx.get('sync_opr') == 'update':
            mappedTempltObjs = mappedObj.filtered(
                lambda obj: obj.need_sync == 'Yes' and
                int(obj.template_name.id) in templateIds)
            return mappedTempltObjs
        return False

    @api.model
    def assign_attribute_Set(self, templateObjs):
        connection = self.env['magento.configure']._create_connection()
        if connection:
            for templateObj in templateObjs:
                attributeLineObjs = templateObj.attribute_line_ids
                setObj = self.get_default_attribute_set()
                if attributeLineObjs:
                    setObj = self.get_magento_attribute_set(
                        attributeLineObjs)
                if setObj:
                    templateObj.write({'attribute_set_id': setObj.id})
                else:
                    return False
        else:
            raise UserError(_("Connection Error!\nError in Odoo Connection"))
        return True

    @api.model
    def get_default_attribute_set(self):
        defaultAttrset = self.env['magento.attribute.set'].search(
            [('set_id', '=', 4), ('instance_id', '=', self._context['instance_id'])], limit=1)
        if not defaultAttrset:
            raise UserError(
                _('Information!\nDefault Attribute set not Found, please sync all Attribute set from Magento!!!'))
        return defaultAttrset

    @api.model
    def get_magento_attribute_set(self, attributeLineObjs):
        flag = False
        templateAttributeIds = []
        attrSetModel = self.env['magento.attribute.set']
        for attr in attributeLineObjs:
            templateAttributeIds.append(attr.attribute_id.id)
        attrSetObjs = attrSetModel.search(
            [('instance_id', '=', self._context['instance_id'])], order="set_id asc")
        for attrSetObj in attrSetObjs:
            setAttributeIds = attrSetObj.attribute_ids.ids
            commonAttributes = sorted(
                set(setAttributeIds) & set(templateAttributeIds))
            templateAttributeIds.sort()
            if commonAttributes == templateAttributeIds:
                return attrSetObj
        return False

    @api.multi
    def export_product_check(self):
        text1 = text2 = text3 = text4 = ''
        updtErrorIds, errorIds = [], []
        successExpIds, successUpdtIds, templateIds = [], [], []
        connection = self.env['magento.configure']._create_connection()
        if connection:
            syncHistoryModel = self.env['magento.sync.history']
            templateModel = self.env['product.template']
            url = connection[0]
            token = connection[1]
            ctx = dict(self._context or {})
            instanceId = ctx['instance_id'] = connection[2]
            domain = [('instance_id', '=', instanceId)]
            if ctx.get('active_model') == "product.template":
                templateIds = self._context.get('active_ids')
            else:
                templateIds = templateModel.search(
                    [('type', '!=', 'service')]).ids
            if not templateIds:
                raise UserError(
                    _('Information!\nNo new product(s) Template found to be Sync.'))

            connectionObj = self.env[
                'magento.configure'].browse(instanceId)
            warehouseId = connectionObj.warehouse_id.id
            ctx['warehouse'] = warehouseId
            if ctx.get('sync_opr') == 'export':
                notMappedTemplateIds = self.with_context(
                    ctx).get_sync_template_ids(templateIds)
                if not notMappedTemplateIds:
                    raise UserError(
                        _('Information!\nListed product(s) has been already exported on magento.'))
                for templateObj in templateModel.with_context(
                        ctx).browse(notMappedTemplateIds):
                    prodType = templateObj.type
                    if prodType == 'service':
                        errorIds.append(templateObj.id)
                        continue
                    expProduct = self.with_context(
                        ctx)._export_specific_template(templateObj, url, token)
                    if expProduct[0] > 0:
                        successExpIds.append(templateObj.id)
                    else:
                        errorIds.append(expProduct[1])
            if ctx.get('sync_opr') == 'update':
                updtMappedTemplateObjs = self.with_context(
                    ctx).get_sync_template_ids(templateIds)
                if not updtMappedTemplateObjs:
                    raise UserError(
                        _('Information!\nListed product(s) has been already updated on magento.'))
                for mappedTempObj in updtMappedTemplateObjs:
                    prodUpdate = self.with_context(ctx)._update_specific_product_template(
                        mappedTempObj, url, token)
                    if prodUpdate[0] > 0:
                        successUpdtIds.append(prodUpdate[1])
                    else:
                        updtErrorIds.append(prodUpdate[1])
            if successExpIds:
                text1 = "\nThe Listed product(s) %s successfully created on Magento." % (
                    successExpIds)
                syncHistoryModel.create(
                    {'status': 'yes', 'action_on': 'product', 'action': 'b', 'error_message': text1})
            if errorIds:
                text2 = '\nThe Listed Product(s) %s does not synchronized on magento.' % errorIds
                syncHistoryModel.create(
                    {'status': 'no', 'action_on': 'product', 'action': 'b', 'error_message': text2})
            if successUpdtIds:
                text3 = '\nThe Listed Product(s) %s has been successfully updated to Magento. \n' % successUpdtIds
                syncHistoryModel.create(
                    {'status': 'yes', 'action_on': 'product', 'action': 'c', 'error_message': text3})
            if updtErrorIds:
                text4 = '\nThe Listed Product(s) %s does not updated on magento.' % updtErrorIds
                syncHistoryModel.create(
                    {'status': 'no', 'action_on': 'product', 'action': 'c', 'error_message': text4})
            dispMsz = text1 + text2 + text3 + text4
            return self.display_message(dispMsz)
    #############################################
    ##          Specific template sync         ##
    #############################################

    def _export_specific_template(self, templateObj, url, token):
        if templateObj:
            mageSetId = 0
            ctx = dict(self._context or {})
            instanceId = ctx.get('instance_id')
            getProductData = {}
            mageAttributeIds = []
            mapTmplModel = self.env['magento.product.template']
            attrPriceModel = self.env['product.template.attribute.value']
            templateId = templateObj.id
            templateSku = templateObj.default_code or 'Template Ref %s' % templateId
            if not templateObj.product_variant_ids:
                return [-2, str(templateId) + ' No Variant Ids Found!!!']
            else:
                if not templateObj.attribute_set_id.id:
                    res = self.assign_attribute_Set([templateObj])
                    if not res:
                        return [-1, str(templateId) +
                                ' Attribute Set Name not matched with attributes!!!']

                attrSetObj = templateObj.attribute_set_id
                attrSetObj = self.with_context(
                    ctx)._check_valid_attribute_set(attrSetObj, templateId)
                if not attrSetObj:
                    return [-1, str(templateId) +
                            ' Matching attribute set not found for this instance!!!']
                wkAttrLineObjs = templateObj.attribute_line_ids
                if not wkAttrLineObjs:
                    templateSku = 'single_variant'
                    mageProdIds = self.with_context(ctx)._sync_template_variants(
                        templateObj, templateSku, url, token)
                    name = templateObj.name
                    price = templateObj.list_price or 0.0
                    if mageProdIds:
                        odooMapData = {
                            'template_name': templateId,
                            'erp_template_id': templateId,
                            'mage_product_id': mageProdIds[0],
                            'base_price': price,
                            'is_variants': False,
                            'instance_id': instanceId
                        }
                        mapTmplModel.with_context(ctx).create(odooMapData)
                        return [1, mageProdIds[0]]
                    else:
                        return [0, templateId]
                else:
                    checkAttribute = self.with_context(
                        ctx)._check_attribute_with_set(attrSetObj, wkAttrLineObjs)
                    if checkAttribute[0] == -1:
                        return checkAttribute
                    mageSetId = templateObj.attribute_set_id.set_id
                    if not mageSetId:
                        return [-3, str(templateId) +
                                ' Attribute Set Name not found!!!']
                    else:
                        for attrLineObj in wkAttrLineObjs:
                            mageAttrIds = self.with_context(
                                ctx)._check_attribute_sync(attrLineObj)
                            if not mageAttrIds:
                                return [-1, str(templateId) +
                                        ' Attribute not syned at magento!!!']
                            valDict = self.with_context(ctx)._search_single_values(
                                templateId, attrLineObj.attribute_id.id)
                            if valDict:
                                ctx.update(valDict)
                            domain = [('product_tmpl_id', '=', templateId)]
                        custom_attributes = [dict(attribute_code='tax_class_id',value=0)]
                        mageProdIds = self.with_context(ctx)._sync_template_variants(
                            templateObj, templateSku, url, token)
                        optionsData = self._create_product_attribute_option(
                            wkAttrLineObjs)
                        stockData = {
                            'is_in_stock': True
                        }
                        extension_attributes = {
                            'configurable_product_links': mageProdIds,
                            'configurable_product_options': optionsData,
                            'stock_item': stockData
                        }
                        getProductData.update(
                            attribute_set_id=mageSetId,
                            visibility=4,
                            price=templateObj.list_price or 0.00,
                            sku='Template sku %s' % templateId,
                            type_id='configurable',
                            custom_attributes=custom_attributes,
                            extension_attributes=extension_attributes
                        )
                        getProductData = self.with_context(ctx)._get_product_array(
                            url, token, templateObj, getProductData)
                        templateObj.write({'prod_type': 'configurable'})
                        productData = {"product": getProductData}
                        prodResponse = self.callMagentoApi(
                            baseUrl=url,
                            url='/V1/products',
                            method='post',
                            token=token,
                            data=productData
                        )
                        if prodResponse and prodResponse.get('id'):
                            magProdId = prodResponse['id']
                            odooMapData = dict(
                                template_name=templateId,
                                erp_template_id=templateId,
                                mage_product_id=magProdId,
                                base_price=getProductData['price'],
                                is_variants=True,
                                instance_id=instanceId
                            )
                            mapTmplModel.with_context(ctx).create(odooMapData)
                            mapData = {'template': {
                                'magento_id': magProdId, 
                                'odoo_id': templateId, 
                                'created_by': 'Odoo'
                            }}
                            mapResponse = self.callMagentoApi(
                                baseUrl=url,
                                url='/V1/odoomagentoconnect/template',
                                method='post',
                                token=token,
                                data=mapData
                            )
                            return [1, magProdId]
                        else:
                            return [
                                0, str(templateId) + " Error during parent sync."]
        else:
            return False

    def _create_product_attribute_option(self, wkAttrLineObjs):
        optionsData = []
        ctx = dict(self._context or {})
        attrValMapModel = self.env['magento.product.attribute.value']
        for typeObj in wkAttrLineObjs:
            getProductOptionData = {}
            mageAttrIds = self.with_context(
                ctx)._check_attribute_sync(typeObj)
            if not mageAttrIds :
                continue
            getProductOptionData['attribute_id'] = mageAttrIds[0]
            getProductOptionData['label'] = typeObj.attribute_id.name
            getProductOptionData['position'] = 0
            getProductOptionData['isUseDefault'] = True
            getProductOptionData['values'] = []
            for valueId in typeObj.value_ids.ids:
                typeSearch = attrValMapModel.search(
                    [('name', '=', valueId)], limit=1)
                if typeSearch:
                    getProductOptionData['values'].append(
                        {"value_index": typeSearch.mage_id})
            optionsData.append(getProductOptionData)
        return optionsData

    def _check_valid_attribute_set(self, attrSetObj, templateId):
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        if instanceId and instanceId == attrSetObj.instance_id.id:
            return attrSetObj
        return False

    ############# sync template variants ########
    def _sync_template_variants(self, templateObj, templateSku, url, token):
        mageVariantIds = []
        mapProdModel = self.env['magento.product']
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        domain = [('instance_id', '=', instanceId)]
        for vrntObj in templateObj.product_variant_ids:
            searchDomain = domain + [('pro_name', '=', vrntObj.id)]
            existMapObj = mapProdModel.search(searchDomain, limit=1)
            if existMapObj:
                mageVariantIds.append(existMapObj.mag_product_id)
            else:
                mageVrntId = self._export_specific_product(
                    vrntObj, templateSku, url, token)
                if mageVrntId and mageVrntId.get('id'):
                    mageVariantIds.append(mageVrntId['id'])
        return mageVariantIds

    ############# check single attribute lines ########
    def _search_single_values(self, templId, attrId):
        dic = {}
        attrLineModel = self.env['product.template.attribute.line']
        attrLineObj = attrLineModel.search(
            [('product_tmpl_id', '=', templId), ('attribute_id', '=', attrId)], limit=1)
        if attrLineObj:
            if len(attrLineObj.value_ids) == 1:
                dic[attrLineObj.attribute_id.name] = attrLineObj.value_ids.name
        return dic

    ############# check attributes lines and set attributes are same ########
    def _check_attribute_with_set(self, attrSetObj, attrLineObjs):
        setAttrObjs = attrSetObj.attribute_ids
        if not setAttrObjs:
            return [-1, str(attrSetObj.name) +
                    ' Attribute Set Name has no attributes!!!']
        setAttrList = list(setAttrObjs.ids)
        for attrLineObj in attrLineObjs:
            if attrLineObj.attribute_id.id not in setAttrList:
                return [-1, str(attrSetObj.name) +
                        ' Attribute Set Name not matched with attributes!!!']
        return [1, '']

    ############# check attributes syned return mage attribute ids ########
    def _check_attribute_sync(self, attrLineObj):
        mapAttrModel = self.env['magento.product.attribute']
        mageAttributeIds = []
        mageId = mapAttrModel.search(
            [('name', '=', attrLineObj.attribute_id.id)], limit=1).mage_id
        if mageId:
            mageAttributeIds.append(mageId)
        return mageAttributeIds

    ############# fetch product details ########
    def _get_product_array(self, url, token, prodObj, getProductData):
        prodCategs = []
        for categobj in prodObj.categ_ids:
            mageCategId = self.sync_categories(url, token, categobj)
            if mageCategId:
                prodCategs.append(mageCategId)
        status = 2
        if prodObj.sale_ok:
            status = 1
        getProductData.update(
            name=prodObj.name,
            weight=prodObj.weight or 0.00,
            status=status
        )
        custom_attributes = [
            {"attribute_code": "description", "value": prodObj.description},
            {"attribute_code": "short_description", "value": prodObj.description_sale},
            {"attribute_code": "category_ids", "value": prodCategs},
            {"attribute_code": "cost", "value": prodObj.standard_price or 0.00}
        ]
        if 'custom_attributes' not in getProductData :
            getProductData['custom_attributes']=custom_attributes
        else :
            getProductData['custom_attributes']+=custom_attributes
        imageData = self._get_product_media(prodObj)
        if imageData:
            getProductData.update(media_gallery_entries=[imageData])
        return getProductData

    def _get_product_qty(self, prodObj, stockItemId=False, stockId=1):
        mobStockAction = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_magento_connect.mob_stock_action'
        )
        productQty, stock = 0, 0
        if mobStockAction and mobStockAction == "qoh":
            productQty = prodObj.qty_available - prodObj.outgoing_qty
        else:
            productQty = prodObj.virtual_available
        if productQty:
            stock = True
        stockData = {
            'stock_id': 1,
            'qty': productQty,
            'is_in_stock': stock
        }
        if stockItemId :
            stockData.update(itemId=stockItemId)
        return stockData

    def _get_product_media(self, prodObj):
        proImage = prodObj.image
        if proImage:
            image_stream = io.BytesIO(codecs.decode(proImage, 'base64'))
            image = Image.open(image_stream)
            imageType = image.format.lower()
            if not imageType:
                imageType = 'jpeg'
            magentoImageType = "image/" + imageType
            imageData = {
                'position': 1,
                'media_type': 'image',
                'disabled': False,
                'label': '',
                'types': ["image", "small_image", "thumbnail", "swatch_image"],
                'content': {
                    'base64_encoded_data': proImage.decode("utf-8"), 
                    'type': magentoImageType, 
                    'name': 'OdooProductImage'
                }
            }
            return imageData
        else :
            return False

    #############################################
    ##          Specific product sync          ##
    #############################################
    def _export_specific_product(self, vrntObj, templateSku, url, token):
        """
        @param code: product Id.
        @param context: A standard dictionary
        @return: list
        """
        getProductData = {}
        priceExtra = 0
        prodAttrPriceModel = self.env['product.template.attribute.value']
        attrMapModel = self.env['magento.product.attribute']
        attrValMapModel = self.env['magento.product.attribute.value']
        domain = [('product_tmpl_id', '=', vrntObj.product_tmpl_id.id)]
        if vrntObj:
            custom_attributes = []
            sku = vrntObj.default_code or 'Ref %s' % vrntObj.id
            prodVisibility = 1
            if templateSku == "single_variant":
                prodVisibility = 4
            if vrntObj.type in ['product', 'consu']:
                prodtype = 'simple'
            else:
                prodtype = 'virtual'
            mageSetId = vrntObj.product_tmpl_id.attribute_set_id.set_id
            if vrntObj.attribute_value_ids:
                for valueObj in vrntObj.attribute_value_ids:
                    mageAttributeCode = attrMapModel.search(
                        [('name', '=', valueObj.attribute_id.id)],limit=1).mage_attribute_code or False
                    mageValueId = attrValMapModel.search(
                        [('name', '=', valueObj.id)],limit=1).mage_id or 0
                    if mageAttributeCode and mageValueId:
                        custom_attributes.append({
                            "attribute_code": mageAttributeCode, 
                            "value": mageValueId
                        })
                    searchDomain = domain + [('product_attribute_value_id', '=', valueObj.id)]
                    attrValPriceObj = prodAttrPriceModel.search(searchDomain, limit=1)
                    if attrValPriceObj:
                        priceExtra += attrValPriceObj.price_extra
            custom_attributes.append({"attribute_code": 'tax_class_id', "value": 0}) 
            stockData = self._get_product_qty(vrntObj)
            extension_attributes = {'stock_item': stockData}
            getProductData.update(
                attribute_set_id=mageSetId,
                type_id=prodtype,
                visibility=prodVisibility,
                sku=sku,
                price=vrntObj.list_price + priceExtra or 0.00,
                custom_attributes=custom_attributes,
                extension_attributes=extension_attributes
            )
            getProductData = self._get_product_array(
                url, token, vrntObj, getProductData)
            vrntObj.write({'prod_type': prodtype, 'default_code': sku})
            magProd = self.prodcreate(url, token, vrntObj,
                                      prodtype, sku, getProductData)
            return magProd

    #############################################
    ##          single products create         ##
    #############################################

    def prodcreate(self, url, token, vrntObj,
            prodtype, sku, getProductData):
        stock = 0
        quantity = 0
        odooProdId = vrntObj.id
        productData = {"product": getProductData}
        prodResponse = self.callMagentoApi(
            baseUrl=url,
            url='/V1/products',
            method='post',
            token=token,
            data=productData
        )
        if prodResponse and prodResponse.get('id'):
            mageProdId = prodResponse.get('id')
            magentoStockId = prodResponse['extension_attributes']['stock_item']['item_id']
            odooMapData = dict(
                pro_name=odooProdId,
                oe_product_id=odooProdId,
                mag_product_id=mageProdId,
                instance_id=self._context.get('instance_id'),
                magento_stock_id=magentoStockId
            )
            self.env['magento.product'].create(odooMapData)
            mapData = {'product': {'magento_id': mageProdId, 'odoo_id': odooProdId, 'created_by': 'Odoo'}}
            mapResponse = self.callMagentoApi(
                baseUrl=url,
                url='/V1/odoomagentoconnect/product',
                method='post',
                token=token,
                data=mapData
            )
        return prodResponse

    #############################################
    ##      update specific product template   ##
    #############################################
    def _update_specific_product_template(self, mappedObj, url, token):
        ctx = dict(self._context or {})
        getProductData = {}
        tempObj = mappedObj.template_name
        mageProdIds = []
        mageProdId = mappedObj.mage_product_id
        mapProdModel = self.env['magento.product']
        domain = [('instance_id', '=', ctx.get('instance_id'))]
        if tempObj and mageProdId:
            if tempObj.product_variant_ids:
                templateSku = tempObj.default_code or 'Template Ref %s' % tempObj.id
                mageProdIds = self._sync_template_variants(
                    tempObj, templateSku, url, token)
                for vrntObj in tempObj.product_variant_ids:
                    searchDomain = domain + [('pro_name', '=', vrntObj.id)]
                    prodMapObj = mapProdModel.search(searchDomain, limit=1)
                    if prodMapObj:
                        updtProdIds = self._update_specific_product(
                            prodMapObj, url, token)
            else:
                return [-1, str(tempObj.id) + ' No Variant Ids Found!!!']
            if mappedObj.is_variants and mageProdIds:
                wkAttrLineObjs = tempObj.attribute_line_ids
                getProductData = self._get_product_array(
                    url, token, tempObj, getProductData)
                optionsData = self._create_product_attribute_option(
                    wkAttrLineObjs)
                stockData = {
                    'is_in_stock': True
                }
                extension_attributes = getProductData.get('extension_attributes', {})
                extension_attributes.update({
                    'configurable_product_links': mageProdIds,
                    'configurable_product_options': optionsData,
                    'stock_item': stockData
                })
                getProductData.update(
                    price=tempObj.list_price or 0.00,
                    extension_attributes=extension_attributes,
                    id=mageProdId
                )
                productData = {"product": getProductData}
                prodResponse = self.callMagentoApi(
                    baseUrl=url,
                    url="/V1/odoomagentoconnect/products",
                    method='post',
                    token=token,
                    data=productData
                )
            mappedObj.need_sync = 'No'
            return [1, tempObj.id]

    #############################################
    ##          update specific product        ##
    #############################################
    def _update_specific_product(self, prodMapObj, url, token):
        getProductData = {}
        prodObj = prodMapObj.pro_name
        mageProdId = prodMapObj.mag_product_id
        instanceId = prodMapObj.instance_id
        stockItemId = prodMapObj.magento_stock_id
        prodAttrPriceModel = self.env['product.template.attribute.value']
        attrMapModel = self.env['magento.product.attribute']
        attrValMapModel = self.env['magento.product.attribute.value']
        domain = [('product_tmpl_id', '=', prodObj.product_tmpl_id.id)]
        if prodObj and mageProdId:
            priceExtra = 0
            custom_attributes = []
            if prodObj.attribute_value_ids:
                for valueObj in prodObj.attribute_value_ids:
                    mageAttributeCode = attrMapModel.search(
                        [('name', '=', valueObj.attribute_id.id)],limit=1).mage_attribute_code or False
                    mageValueId = attrValMapModel.search(
                        [('name', '=', valueObj.id)],limit=1).mage_id or 0
                    if mageAttributeCode and mageValueId:
                        custom_attributes.append({
                            "attribute_code": mageAttributeCode, 
                            "value": mageValueId
                        })
                    searchDomain = domain + [('product_attribute_value_id', '=', valueObj.id)]
                    attrValPriceObj = prodAttrPriceModel.search(searchDomain, limit=1)
                    if attrValPriceObj:
                        priceExtra += attrValPriceObj.price_extra
            getProductData.update(
                price=prodObj.list_price + priceExtra or 0.00,
                custom_attributes=custom_attributes
            )
            getProductData = self._get_product_array(
                url, token, prodObj, getProductData)
            if instanceId.inventory_sync == 'enable':
                stockData = self._get_product_qty(prodObj)
                extension_attributes = getProductData.get('extension_attributes', {})
                extension_attributes.update(stock_item=stockData)
                getProductData['extension_attributes'] = extension_attributes

            productSku = prodObj.default_code
            try:
                productSku = quote(productSku, safe='')
            except Exception as e:
                productSku = quote(productSku.encode("utf-8"), safe='')
            productData = {"product": getProductData}
            prodResponse = self.callMagentoApi(
                baseUrl=url,
                url="/V1/products/" + str(productSku),
                method='put',
                token=token,
                data=productData
            )
            if prodResponse:
                prodMapObj.need_sync = 'No'
            return [1, prodObj.id]
