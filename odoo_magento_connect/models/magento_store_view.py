# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################


from odoo import api, fields, models


class MagentoStoreView(models.Model):
    _name = "magento.store.view"
    _description = "Magento Store View"

    name = fields.Char(string='Store View Name', size=64, required=True)
    code = fields.Char(string='Code', size=64, required=True)
    view_id = fields.Integer(string='Magento Store View Id', readonly=True)
    instance_id = fields.Many2one(
        'magento.configure', string='Magento Instance')
    group_id = fields.Many2one('magento.store', string='Store Id')
    create_date = fields.Datetime(string='Created Date', readonly=True)

    @api.multi
    @api.depends('name', 'group_id')
    def name_get(self):
        result = []
        for record in self:
            name = record.name + \
                "\n(%s)" % (record.group_id.name) + \
                "\n(%s)" % (record.group_id.website_id.name)
            result.append((record.id, name))
        return result

    @api.model
    def _get_store_view(self, url, token):
        storeViewId = False
        instanceId = self._context.get('instance_id')
        magentoStoreViews = []
        storeViewsResponse = self.env['magento.synchronization'].callMagentoApi(
            baseUrl=url,
            url='/V1/store/storeViews',
            method='get',
            token=token
        )
        if storeViewsResponse :
            magentoStoreViews = storeViewsResponse
            self.env['magento.store']._get_store_group(url, token)
        for magentoStoreView in magentoStoreViews:
            if not magentoStoreView.get('id'):
                continue
            storeviewObjs = self.search(
                [('view_id', '=', magentoStoreView['id']), ('instance_id', '=', instanceId)])
            if storeviewObjs:
                storeviewObj = storeviewObjs[0]
            else:
                groupObj = self.env['magento.store'].search(
                    [('group_id', '=', magentoStoreView['store_group_id']), ('instance_id', '=', instanceId)])
                if groupObj:
                    groupId = groupObj[0].id
                viewDict = {
                    'name': magentoStoreView['name'],
                    'code': magentoStoreView['code'],
                    'view_id': magentoStoreView['id'],
                    'group_id': groupId,
                    'instance_id': instanceId,
                }
                storeviewObj = self.create(viewDict)
            storeViewId = storeviewObj.id
        return storeViewId
