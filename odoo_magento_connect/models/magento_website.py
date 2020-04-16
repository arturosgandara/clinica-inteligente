# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class MagentoWebsite(models.Model):
    _name = "magento.website"
    _description = "Magento Website"

    name = fields.Char(string='Website Name', size=64, required=True)
    website_id = fields.Integer(string='Magento Webiste Id', readonly=True)
    instance_id = fields.Many2one(
        'magento.configure', string='Magento Instance')
    code = fields.Char(string='Code', size=64, required=True)
    default_group_id = fields.Integer(string='Default Store', readonly=True)
    create_date = fields.Datetime(string='Created Date', readonly=True)

    @api.model
    def _get_website(self, url, token):
        websiteId = False
        instanceId = self._context.get('instance_id')
        magentoWebsites = []
        storesResponse = self.env['magento.synchronization'].callMagentoApi(
            baseUrl=url,
            url='/V1/store/websites',
            method='get',
            token=token
        )
        if storesResponse :
            magentoWebsites = storesResponse
        for magentoWebsite in magentoWebsites:
            if not magentoWebsite.get('id'):
                continue
            websiteObjs = self.search(
                [('website_id', '=', magentoWebsite['id']), ('instance_id', '=', instanceId)])
            if websiteObjs:
                websiteObj = websiteObjs
            else:
                websiteDict = {
                    'name': magentoWebsite['name'],
                    'code': magentoWebsite['code'],
                    'instance_id': instanceId,
                    'website_id': magentoWebsite['id'],
                    'default_group_id': magentoWebsite['default_group_id']
                }
                websiteObj = self.create(websiteDict)
            websiteId = websiteObj.id
        return websiteId
