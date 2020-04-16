# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _handle_first_contact_creation(self):
        """ On creation of first contact for a company (or root) that has no address, assume contact address
        was meant to be company address """
        parent = self.parent_id
        address_fields = self._address_fields()
        if parent and (
            parent.is_company or not parent.parent_id) and len(
            parent.child_ids) == 1 and any(
            self[f] for f in address_fields) and not any(
                parent[f] for f in address_fields):
            addr_vals = self._update_fields_values(address_fields)
            parent.update_address(addr_vals)

    wk_company = fields.Char(string='Company', size=128)
