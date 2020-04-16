# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import json

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MessageWizard(models.TransientModel):
    _name = "message.wizard"

    text = fields.Text(string='Message', readonly=True, translate=True)


class RegionWizard(models.TransientModel):
    _name = "region.wizard"

    country_ids = fields.Many2one('res.country', string='Country')

    @api.model
    def _sync_mage_region(self, url, token, countryCode):
        regionData = {}
        stateData = {}
        try:
            regionResponse = self.env['magento.synchronization'].callMagentoApi(
                url='/V1/directory/countries/' + str(countryCode),
                method='get',
                token=token,
                baseUrl=url
            )
            if not regionResponse:
                raise UserError(
                    _("Requested country is not available at Magento %r " % str(countryCode)))
            regionData = regionResponse
        except Exception as e:
            raise UserError(_('Error %s') % e)
        if regionData:
            regionDict = {
                'name': regionData['full_name_english'],
                'region_code': regionData['id'],
                'country_code': countryCode
            }
            self.env['magento.region'].create(regionDict)
            if countryCode != 'US':
                countryObjs = self.env['res.country'].search(
                    [('code', '=', countryCode)])
                stateDict = {
                    'name': regionData['full_name_english'],
                    'country_id': countryObjs[0].id,
                    'code': regionData['three_letter_abbreviation']
                }
                self.env['res.country.state'].create(stateDict)
            return len(regionData)
        else:
            return 0

    @api.one
    def sync_state(self):
        connectionObjs = self.env['magento.configure'].search(
            [('active', '=', True)])
        if len(connectionObjs) > 1:
            raise UserError(
                _('Error!\nSorry, only one Active Configuration setting is allowed.'))
        if not connectionObjs:
            raise UserError(
                _('Error!\nPlease create the configuration part for connection!!!'))
        else:
            connection = self.env['magento.configure']._create_connection()
            if connection:
                url = connection[0]
                token = connection[1]
                ctx = dict(self._context or {})
                ctx['instance_id'] = connection[2]
                if token:
                    countryId = self.country_ids
                    countryCode = countryId.code
                    mapObjs = self.env['magento.region'].search(
                        [('country_code', '=', countryCode)])
                    if not mapObjs:
                        totalRegionSynced = self._sync_mage_region(
                            url, token, countryCode)
                        if totalRegionSynced == 0:
                            raise UserError(
                                _('Error!\n There is no any region exist for country %s.') %
                                (countryId.name))
                            return {
                                'type': 'ir.actions.act_window_close',
                            }
                        else:
                            text = "%s Region of %s are sucessfully Imported to Odoo." % (
                                totalRegionSynced, countryId.name)
                            return self.env['magento.synchronization'].display_message(text)
                    else:
                        raise UserError(
                            _('Information!\nAll regions of %s are already imported to Odoo.') %
                            (countryId.name))
