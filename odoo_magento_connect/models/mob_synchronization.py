# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import json
import logging
import requests

from odoo import api, models
from odoo.http import request

_logger = logging.getLogger(__name__)

class MagentoSynchronization(models.TransientModel):
    _name = "magento.synchronization"
    _description = "Magento Synchronization"

    @api.multi
    def open_configuration(self):
        connectionId = self.env['magento.configure'].search(
            [('active', '=', True)], limit=1).id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configure Magento Api',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'magento.configure',
            'res_id': connectionId,
            'target': 'current',
            'domain': '[]',
        }

    def display_message(self, message):
        wizardObj = self.env['message.wizard'].create({'text': message})
        return {
            'name': ("Information"),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'message.wizard',
            'view_id': self.env.ref('odoo_magento_connect.message_wizard_form1').id,
            'res_id': wizardObj.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
        }

    @api.model
    def sync_attribute_set(self, data):
        ctx = dict(self._context or {})
        res = False
        attrSetModel = self.env['magento.attribute.set']
        setName = data.get('name')
        setId = data.get('set_id', 0)
        if setName and setId:
            instanceId = ctx.get('instance_id', False)
            setMapObj = attrSetModel.search([
                    ('set_id', '=', setId),
                    ('instance_id', '=', instanceId)
                ], limit=1)
            if not setMapObj:
                setDict = {
                    'name': setName,
                    'set_id': setId,
                    'created_by': 'Magento',
                    'instance_id': instanceId
                }
                setMapObj = attrSetModel.create(setDict)
            if setMapObj:
                updateDict = {
                    'name': setName
                }
                attributeIds = data.get('attribute_ids',[])
                if attributeIds:
                    updateDict['attribute_ids'] = [
                        (6, 0, attributeIds)]
                else:
                    updateDict['attribute_ids'] = [[5]]
                res = setMapObj.write(updateDict)
        return res


    def get_mage_region_id(self, url, token, region, countryCode):
        """
        @return magneto region id
        """
        regionModel = self.env['magento.region']
        searchDomain = [('country_code', '=', countryCode)]
        mapObjs = regionModel.search(searchDomain)
        if not mapObjs:
            returnId = self.env['region.wizard']._sync_mage_region(
                url, token, countryCode)
        searchDomain += [('name', '=', region)]
        return regionModel.search(searchDomain, limit=1).mag_region_id

    @api.multi
    def reset_mapping(self, instanceId=None):
        instanceId = self.env['magento.configure'].search(
            [('active', '=', True)], limit=1).id
        domain = [('instance_id', '=', instanceId)]
        message = 'All '
        regionObjs = self.env['magento.region'].search([])
        if regionObjs:
            regionObjs.unlink()
            message += 'region, '
        categObjs = self.env['magento.category'].search(domain)
        if categObjs:
            categObjs.unlink()
            message += 'category, '
        prodAttrObjs = self.env['magento.product.attribute'].search(domain)
        if prodAttrObjs:
            prodAttrObjs.unlink()
            message += 'product attribute, '
        prodAttrValObjs = self.env['magento.product.attribute.value'].search(
            domain)
        if prodAttrValObjs:
            prodAttrValObjs.unlink()
            message += 'attribute value, '
        attrSetObjs = self.env['magento.attribute.set'].search(domain)
        if attrSetObjs:
            attrSetObjs.unlink()
            message += 'attribute set, '
        prodTempObjs = self.env['magento.product.template'].search(domain)
        if prodTempObjs:
            prodTempObjs.unlink()
        prodObjs = self.env['magento.product'].search(domain)
        if prodObjs:
            prodObjs.unlink()
            message += 'product, '
        partnerObjs = self.env['magento.customers'].search(domain)
        if partnerObjs:
            partnerObjs.unlink()
            message += 'customers, '
        orderObjs = self.env['wk.order.mapping'].search(domain)
        if orderObjs:
            orderObjs.unlink()
            message += 'order, '
        historyObjs = self.env['magento.sync.history'].search([])
        if historyObjs:
            historyObjs.unlink()
        if len(message) > 4:
            message += 'mappings has been deleted successfully'
        else:
            message = "No mapping entry exist"
        return self.display_message(message)

    @api.model
    def callMagentoApi(self, url, method, token='', data={}, params=[], filter=[], baseUrl=''):
        _logger.debug("Call %r : %r ",method.upper(),url)
        action = 'a'
        connectionModel = self.env['magento.configure']
        if not token :
            connection = connectionModel._create_connection()
            if connection:
                baseUrl = connection[0]
                token = connection[1]
        if not baseUrl:
            if self._context.get('instance_id'):
                connectionObj = connectionModel.browse(self._context.get('instance_id'))
            else :
                connectionObj = connectionModel.search([('active', '=', True)], limit=1)
            baseUrl = connectionObj.name

        apiUrl = baseUrl + "/index.php/rest" + url
        token = token.replace('"', "")
        userAgent = request.httprequest.environ.get('HTTP_USER_AGENT', '')
        headers = {'Authorization': token,
                    'Content-Type': 'application/json', 'User-Agent': userAgent}

        if method == 'get' :
            response = requests.get(
                apiUrl, headers=headers, verify=False, params=params)
        elif method == 'post' :
            action = 'b'
            payload = json.dumps(data)
            response = requests.post(
                apiUrl, headers=headers, data=payload, verify=False, params=params)
        elif method == 'put' :
            action = 'c'
            payload = json.dumps(data)
            response = requests.put(
                apiUrl, headers=headers, data=payload, verify=False, params=params)
        elif method == 'delete' :
            response = requests.delete(
                apiUrl, headers=headers, verify=False, params=params)
        else :
            return "Wrong API method is selected."
        responseData = json.loads(response.text)
        tmp = json.dumps(responseData,indent=4)
        _logger.debug("Response: "+tmp)
        if not response.ok:
            self.env['magento.sync.history'].create({
                'status': 'no', 
                'action_on': 'api', 
                'action': action, 
                'error_message': "Error in calling api "+ url +" :\n"+responseData.get('message') +
                    "\n"+str(responseData.get('parameters'))
            })
            return {}
        return responseData
        

# END
