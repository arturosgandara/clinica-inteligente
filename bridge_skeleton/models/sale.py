# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    @api.depends('picking_ids', 'order_line.qty_delivered')
    def _shipped_status_compute(self):
        for saleObj in self:
            saleObj.is_shipped = all(
                line.qty_delivered >= line.product_uom_qty
                for line in saleObj.order_line.filtered(lambda l: l.product_id.type != 'service')
            )

    @api.depends('invoice_status')
    def _invoiced_status_compute(self):
        for saleObj in self:
            if saleObj.invoice_status == "invoiced":
                saleObj.is_invoiced = True

    def _get_ecommerces(self):
        return [('test', 'TEST')]
    _ecommerce_selection = lambda self, * \
        args, **kwargs: self._get_ecommerces(*args, **kwargs)

    ecommerce_channel = fields.Selection(
        string='eCommerce Channel',
        selection=_ecommerce_selection,
        help="Name of ecommerce from where this Order is generated.",
        default='test')
    is_shipped = fields.Boolean(compute='_shipped_status_compute')
    is_invoiced = fields.Boolean(compute='_invoiced_status_compute')
