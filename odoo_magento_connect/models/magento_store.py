# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################


from odoo import api, fields, models


class MagentoStore(models.Model):
    _name = "magento.store"
    _description = "Magento Store"

    name = fields.Char(string='Store Name', size=64, required=True)
    group_id = fields.Integer(string='Magento Store Id', readonly=True)
    instance_id = fields.Many2one(
        'magento.configure', string='Magento Instance')
    root_category_id = fields.Integer(string='Root Category Id', readonly=True)
    default_store_id = fields.Integer(string='Default Store Id')
    website_id = fields.Many2one('magento.website', string='Website')
    create_date = fields.Datetime(string='Created Date', readonly=True)

    @api.model
    def _get_store_group(self, url, token):
        groupId = False
        instanceId = self._context.get('instance_id')
        magentoStores = []
        storesResponse = self.env['magento.synchronization'].callMagentoApi(
            baseUrl=url,
            url='/V1/store/storeGroups',
            method='get',
            token=token
        )
        if storesResponse :
            magentoStores = storesResponse
            self.env['magento.website']._get_website(url, token)
        for magentoStore in magentoStores:
            if not magentoStore.get('id'):
                continue
            groupObjs = self.search(
                [('group_id', '=', magentoStore['id']), ('instance_id', '=', instanceId)])
            if groupObjs:
                groupObj = groupObjs[0]
            else:
                websiteObjs = self.env['magento.website'].search(
                    [('website_id', '=', magentoStore['website_id']), ('instance_id', '=', instanceId)])
                if websiteObjs:
                    websiteId = websiteObjs[0].id
                groupDict = {
                    'name': magentoStore['name'],
                    'website_id': websiteId,
                    'group_id': magentoStore['id'],
                    'instance_id': instanceId,
                    'root_category_id': magentoStore['root_category_id'],
                    'default_store_id': magentoStore['default_store_id'],
                }
                groupObj = self.create(groupDict)
            groupId = groupObj.id
        return groupId
