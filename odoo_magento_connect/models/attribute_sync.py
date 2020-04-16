# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, models


class MagentoSynchronization(models.TransientModel):
    _inherit = "magento.synchronization"

    #############################################
    ##   Export Attributes and values          ##
    #############################################

    @api.multi
    def export_attributes_and_their_values(self):
        displayMessage = ''
        attributeCount = 0
        attributeModel = self.env['product.attribute']
        attributeMappingModel = self.env['magento.product.attribute']
        valueMappingModel = self.env['magento.product.attribute.value']
        connection = self.env['magento.configure']._create_connection()
        if connection:
            url = connection[0]
            token = connection[1]
            ctx = dict(self._context or {})
            ctx['instance_id'] = instanceId = connection[2]
            attributeMapObjs = attributeMappingModel.with_context(
                ctx).search([('instance_id', '=', instanceId)])
            mapDict = dict(attributeMapObjs.mapped(lambda mapObj: \
                (mapObj.erp_id,[mapObj.mage_id,mapObj.mage_attribute_code])))
            mapArray = mapDict.keys()
            attributeObjs = attributeModel.search([])
            if attributeObjs:
                for attributeObj in attributeObjs:
                    odooId = attributeObj.id
                    if odooId not in mapArray:
                        name = attributeObj.name
                        attributeCode = name.lower().replace(" ", "_").replace("-", "_")[:29]
                        attributeCode = attributeCode.strip()
                        label = attributeObj.name
                        attributeResponse = self.with_context(ctx).create_product_attribute(
                            url, token, odooId, attributeCode, label)
                    else:
                        mapData = mapDict.get(odooId)
                        mageId = mapData[0]
                        attributeCode = mapData[1]
                        attributeResponse = [1, int(mageId)]
                    if attributeResponse[0] == 0:
                        displayMessage = displayMessage + attributeResponse[1]
                    if attributeResponse[0] > 0:
                        mageId = attributeResponse[1]
                        attributeValueData = {}
                        for valueObj in attributeObj.value_ids:
                            valueName = valueObj.name
                            valueId = valueObj.id
                            attributeValueData[valueName] = valueId
                            if not valueMappingModel.with_context(ctx).search([('erp_id', '=', valueId), ('instance_id', '=', instanceId)], limit=1):
                                position = valueObj.sequence
                                valueResponse = self.with_context(ctx).create_attribute_value(
                                    url, token, attributeCode, valueId, valueName, position)
                        self.with_context(ctx).map_attribute_values(
                            url, token, attributeCode, attributeValueData)
                        attributeCount += 1
            else:
                displayMessage = "No Attribute(s) Found To Be Export At Magento!!!"
            if attributeCount:
                displayMessage += "\n %s Attribute(s) and their value(s) successfully Synchronized To Magento." % (
                    attributeCount)
            return self.display_message(displayMessage)

    @api.model
    def create_product_attribute(self, url, token, odooId, attributeCode, label):
        if token:
            attrributeData = {"attribute": {
                'attributeCode': attributeCode,
                'scope': 'global',
                'frontendInput': 'select',
                'isRequired': 0,
                'frontendLabels': [{'storeId': 0, 'label': label}]
               }
            }
            attributeResponse = self.callMagentoApi(
                baseUrl=url,
                url='/V1/products/attributes',
                method='post',
                token=token,
                data=attrributeData
            )
            mageAttributeId = 0
            if attributeResponse and attributeResponse.get('attribute_id', 0) > 0:
                mageAttributeId = attributeResponse['attribute_id']
                returnData = [1, mageAttributeId]
            else:
                attributeResponse = self.callMagentoApi(
                    baseUrl=url,
                    url='/V1/products/attributes/' + attributeCode,
                    method='get',
                    token=token,
                )
                if attributeResponse and attributeResponse.get('attribute_id') > 0:
                    mageAttributeId = attributeResponse['attribute_id']
                    returnData = [1, mageAttributeId]
                else:
                    returnData = [0, 'Attribute Not found at magento.']
            if mageAttributeId :
                erpMapData = {
                    'name': odooId,
                    'erp_id': odooId,
                    'mage_id': mageAttributeId,
                    'mage_attribute_code':attributeCode, 
                    'instance_id': self._context.get('instance_id'),
                }
                self.env['magento.product.attribute'].create(erpMapData)
                mapData = {'attribute': {
                    'name':attributeCode,
                    'magento_id': mageAttributeId, 
                    'odoo_id': odooId, 
                    'created_by': 'Odoo'
                }}
                self.callMagentoApi(
                    baseUrl=url,
                    url='/V1/odoomagentoconnect/attribute',
                    method='post',
                    token=token,
                    data=mapData
                )
            return returnData

    @api.model
    def create_attribute_value(self, url, token, attributeCode, erpAttrId, name, position='0'):
        if token:
            name = name.strip()
            optionsData = {"option": {
                "label": name,
                "sortOrder": position,
                "isDefault": 0,
                'storeLabels': [{'storeId': 0, 'label': name}]
            }}
            optionResponse = self.callMagentoApi(
                baseUrl=url,
                url='/V1/products/attributes/' + attributeCode + '/options',
                method='post',
                token=token,
                data=optionsData
            )
            return optionResponse

    @api.model
    def map_attribute_values(self, url, token, attributeCode, attributeValueData):
        mapValueModel = self.env['magento.product.attribute.value']
        optionResponse = self.callMagentoApi(
            baseUrl=url,
            url='/V1/products/attributes/' + attributeCode + '/options',
            method='get',
            token=token
        )
        mageIds = optionResponse
        if type(optionResponse) is list:
            for mageOption in optionResponse:
                if mageOption.get('value'):
                    mageId = mageOption['value']
                    mageLabel = mageOption['label']
                    mapValueObj = mapValueModel.search([
                        ('mage_id', '=', int(mageId)), 
                        ('instance_id', '=', self._context.get('instance_id'))
                    ], limit=1)
                    if not mapValueObj and attributeValueData.get(mageLabel):
                        odooId = attributeValueData[mageLabel]
                        erpMapData = {
                            'name': odooId,
                            'erp_id': odooId,
                            'mage_id': int(mageId),
                            'instance_id': self._context.get('instance_id')
                        }
                        mapValueModel.create(erpMapData)
                        mapData = {'option': {
                            'name': mageLabel, 
                            'magento_id': mageId, 
                            'odoo_id': odooId, 
                            'created_by': 'Odoo'
                        }}
                        self.callMagentoApi(
                            url='/V1/odoomagentoconnect/option',
                            method='post',
                            token=token,
                            data=mapData
                        )
        return True
