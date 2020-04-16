# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, models


def _unescape(text):
    ##
    # Replaces all encoded characters by urlib with plain utf8 string.
    #
    # @param text source text.
    # @return The plain text.
    from urllib.parse import unquote_plus
    try:
        text = unquote_plus(text)
        return text
    except Exception as e:
        return text


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        if 'magento' in self._context:
            vals = self.customer_array(vals)
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'magento' in self._context:
            vals = self.customer_array(vals)
        return super(ResPartner, self).write(vals)

    def customer_array(self, data):
        dic = {}
        stateModel = self.env['res.country.state']
        country_code = data.pop('country_code', False)
        if country_code:
            countryObj = self.env['res.country'].search(
                [('code', '=', country_code)], limit=1)
            if countryObj:
                data['country_id'] = countryObj.id
                region = data.pop('region', False)
                if region:
                    region = _unescape(region)
                    stateObj = stateModel.search([
                        ('name', '=', region),
                        ('country_id', '=', countryObj.id)
                    ], limit=1)
                    if stateObj:
                        data['state_id'] = stateObj.id
                    else:
                        dic['name'] = region
                        dic['country_id'] = countryObj.id
                        code = region[:3].upper()
                        temp = code
                        stateObj = stateModel.search(
                            [('code', '=ilike', code)], limit=1)
                        counter = 0
                        while stateObj and counter < 100:
                            code = temp + str(counter)
                            stateObj = stateModel.search(
                                [('code', '=ilike', code)], limit=1)
                            counter = counter + 1
                        if counter == 100:
                            code = region.upper()
                        dic['code'] = code
                        stateObj = stateModel.create(dic)
                        data['state_id'] = stateObj.id
        tag = data.pop('tag', False)
        if tag:
            tag = _unescape(tag)
            tagObjs = self.env['res.partner.category'].search(
                [('name', '=', tag)], limit=1)
            if not tagObjs:
                tagId = self.env['res.partner.category'].create({'name': tag})
            else:
                tagId = tagObjs[0].id
            data['category_id'] = [(6, 0, [tagId])]
        data.pop('mage_customer_id', None)
        if data.get('wk_company'):
            data['wk_company'] = _unescape(data['wk_company'])
        if data.get('name'):
            data['name'] = _unescape(data['name'])
        if data.get('email'):
            data['email'] = _unescape(data['email'])
        if data.get('street'):
            data['street'] = _unescape(data['street'])
        if data.get('street2'):
            data['street2'] = _unescape(data['street2'])
        if data.get('city'):
            data['city'] = _unescape(data['city'])
        return data
