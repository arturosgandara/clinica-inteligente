# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################

from odoo.exceptions import UserError
from odoo import api, fields, models


class MagentoWizard(models.TransientModel):
    _name = "magento.wizard"

    magento_store_view = fields.Many2one(
        'magento.store.view', string='Default Magento Store')

    @api.multi
    def buttun_select_default_magento_store(self):
        self.ensure_one()
        ctx = dict(self._context or {})
        if self._context.get('active_id'):
            connectionObj = self.env['magento.configure'].browse(
                self._context['active_id'])
            connectionObj.store_id = self.magento_store_view.id
        return self.env['magento.synchronization'].display_message(ctx['text'])
