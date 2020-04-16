# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import _, api, models
from odoo.exceptions import UserError


class MagentoSynchronization(models.TransientModel):
    _inherit = "magento.synchronization"

    ########################################
    ##     Category Synchronizations      ##
    ########################################

    @api.model
    def get_map_updt_category_objs(self, categoryObjs):
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        magCategModel = self.env['magento.category']
        mappedCategObjs = magCategModel.search(
            [('instance_id', '=', instanceId)])
        if ctx.get('sync_opr') == 'export':
            mapCategObjs = mappedCategObjs.mapped('cat_name')
            notMappedCategObjs = list(set(categoryObjs) - set(mapCategObjs))
            return notMappedCategObjs
        if ctx.get('sync_opr') == 'update':
            mappedCategObjs = mappedCategObjs.filtered(
                lambda obj: obj.need_sync == 'Yes' and
                int(obj.cat_name.id) in categoryObjs.ids)
            return mappedCategObjs

    @api.multi
    def export_categories_check(self):
        text = text1 = text2 = ''
        updtErrorIds, successIds, successUpdtIds, categoryObjs = [], [], [], []
        connection = self.env['magento.configure']._create_connection()
        if connection:
            categModel = self.env['product.category']
            mageSyncHistoryModel = self.env['magento.sync.history']
            url = connection[0]
            token = connection[1]
            ctx = dict(self._context or {})
            instanceId = ctx['instance_id'] = connection[2]
            if ctx.get('active_model') == "product.category":
                categIds = ctx.get('active_ids')
                categoryObjs = categModel.browse(categIds)
            else:
                categoryObjs = categModel.with_context(ctx).search([])
            if ctx.get('sync_opr') == 'export':
                expCategoryObjs = self.with_context(
                    ctx).get_map_updt_category_objs(categoryObjs)
                if not expCategoryObjs:
                    raise UserError(
                        _('Information!\nAll category(s) has been already exported on magento.'))
                for expCategoryObj in expCategoryObjs:
                    categId = self.with_context(ctx).sync_categories(
                        url, token, expCategoryObj)
                    if categId:
                        successIds.append(expCategoryObj.id)
                text = "\nThe Listed category ids %s has been created on magento." % (
                    sorted(successIds))
                mageSyncHistoryModel.create(
                    {'status': 'yes', 'action_on': 'category', 'action': 'b', 'error_message': text})

            if ctx.get('sync_opr') == 'update':
                updtMapObjs = self.with_context(
                    ctx).get_map_updt_category_objs(categoryObjs)
                if not updtMapObjs:
                    raise UserError(
                        _('Information!\nAll category(s) has been already updated on magento.'))
                categUpdate = self.with_context(ctx)._update_specific_category(
                    updtMapObjs, url, token)
                if categUpdate[0]:
                    successUpdtIds = categUpdate[0]
                    text1 = '\nThe Listed category ids %s has been successfully updated to Magento. \n' % sorted(
                        successUpdtIds)
                    mageSyncHistoryModel.create(
                        {'status': 'yes', 'action_on': 'category', 'action': 'c', 'error_message': text1})
                if categUpdate[1]:
                    updtErrorIds = categUpdate[1]
                    text2 = '\nThe Listed category ids %s does not updated on magento.' % sorted(
                        updtErrorIds)
                    mageSyncHistoryModel.create(
                        {'status': 'no', 'action_on': 'category', 'action': 'c', 'error_message': text2})
            displayMessage = text + text1 + text2
            return self.display_message(displayMessage)
        ########## update specific category ##########

    @api.model
    def _update_specific_category(self, updtMapObjs, url, token):
        cat_mv = False
        updtedCategoryIds, notUpdtedCategoryIds = [], []
        magCategModel = self.env['magento.category']
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        for categMapObj in updtMapObjs:
            categObj = categMapObj.cat_name
            mageId = categMapObj.mag_category_id
            magParentId = 1
            if categObj and mageId:
                updtedCategoryIds.append(categObj.id)
                erpParentId = categObj.parent_id or False
                if erpParentId:
                    existMapObj = magCategModel.search(
                        [('cat_name', '=', erpParentId.id), ('instance_id', '=', instanceId)])
                    if existMapObj:
                        magParentId = existMapObj[0].mag_category_id
                    else:
                        magParentId = self.sync_categories(
                            url, token, erpParentId)
                getCategoryData = {
                    'name': categObj.name,
                    'parent_id': magParentId
                }
                categoryData = {"category": getCategoryData}
                categoryResponse = self.callMagentoApi(
                    baseUrl=url,
                    url='/V1/categories/' + str(mageId),
                    method='put',
                    token=token,
                    data=categoryData
                )
                if categoryResponse :
                    categoryUpdateData = {'categoryId': mageId,'name': categObj.name}
                    self.callMagentoApi(
                        baseUrl=url,
                        url='/V1/odoomagentoconnect/category',
                        method='put',
                        token=token,
                        data=categoryUpdateData
                    )
            else:
                notUpdtedCategoryIds.append(categObj.id)
        updtMapObjs.write({'need_sync': 'No'})
        return [updtedCategoryIds, notUpdtedCategoryIds]

    @api.model
    def sync_categories(self, url, token, erpCategoryObj):
        mageCategoryModel = self.env['magento.category']
        instanceId = 0
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        if erpCategoryObj:
            mappedCategoryObj = mageCategoryModel.search(
                [('cat_name', '=', erpCategoryObj.id), ('instance_id', '=', instanceId)])
            if not mappedCategoryObj:
                name = erpCategoryObj.name
                if erpCategoryObj.parent_id:
                    paretnCategId = self.sync_categories(
                        url, token, erpCategoryObj.parent_id)
                else:
                    paretnCategId = self.create_category(
                        url, token, erpCategoryObj.id, 1, name)
                    if paretnCategId[0] > 0:
                        return paretnCategId[1]
                    else:
                        return False
                magCategoryId = self.create_category(
                    url, token, erpCategoryObj.id, paretnCategId, name)
                if magCategoryId[0] > 0:
                    return magCategoryId[1]
                else:
                    False
            else:
                magCategoryId = mappedCategoryObj[0].mag_category_id
                return magCategoryId
        else:
            return False

    def create_category(self, url, token, erpCatgId, parentId, catgname):
        if erpCatgId < 1:
            return [0, False]
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        categoryData = {"category": {
            'name': catgname,
            'parentId': parentId,
            'isActive': 1,
            'includeInMenu': 1
        }}
        categoryResponse = self.callMagentoApi(
            baseUrl=url,
            url='/V1/categories',
            method='post',
            token=token,
            data=categoryData
        )
        if categoryResponse and categoryResponse.get('id') > 0:
            mageCatgId = categoryResponse.get('id')
            # 	##########  Mapping Entry  ###########
            erpMapData = {
                'cat_name' : erpCatgId,
                'oe_category_id' : erpCatgId,
                'mag_category_id' : mageCatgId,
                'created_by' : 'odoo',
                'instance_id' : instanceId,
            }
            self.env['magento.category'].create(erpMapData)
            mapData = {'category': {
                'magento_id': mageCatgId, 
                'odoo_id': erpCatgId, 
                'created_by': 'Odoo'
            }}
            self.callMagentoApi(
                baseUrl=url,
                url='/V1/odoomagentoconnect/category',
                method='post',
                token=token,
                data=mapData
            )
            return [1, mageCatgId]
        else:
            return [0, categoryResponse]

    #############################################
    ##      End Of Category Synchronizations   ##
    #############################################
