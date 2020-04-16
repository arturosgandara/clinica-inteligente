# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, models


class account_payment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def post(self):
        res = super(account_payment, self).post()
        saleModel = self.env['sale.order']
        enableOrderInvoice = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_magento_connect.mob_sale_order_invoice'
        )
        for rec in self:
            invObjs = rec.invoice_ids
            for invObj in invObjs:
                invInfo = invObj.read(['origin', 'state'])
                if invInfo[0]['origin']:
                    saleObjs = saleModel.search(
                        [('name', '=', invInfo[0]['origin'])])
                    for saleObj in saleObjs:
                        mapObjs = self.env['wk.order.mapping'].search(
                            [('erp_order_id', '=', saleObj.id)])
                        if mapObjs and saleObj.ecommerce_channel == "magento" \
                                and enableOrderInvoice and saleObj.is_invoiced:
                            saleObj.manual_magento_order_operation("invoice")
        return res
