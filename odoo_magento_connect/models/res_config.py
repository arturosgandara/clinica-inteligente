# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mob_discount_product = fields.Many2one(
        'product.product',
        string="Discount Product",
        help="""Service type product used for Discount purposes.""")
    mob_coupon_product = fields.Many2one(
        'product.product',
        string="Coupon Product",
        help="""Service type product used in Coupon.""")
    mob_payment_term = fields.Many2one(
        'account.payment.term',
        string="Magento Payment Term",
        help="""Default Payment Term Used In Sale Order.""")
    mob_sales_team = fields.Many2one(
        'crm.team',
        string="Magento Sales Team",
        help="""Default Sales Team Used In Sale Order.""")
    mob_sales_person = fields.Many2one(
        'res.users',
        string="Magento Sales Person",
        help="""Default Sales Person Used In Sale Order.""")
    mob_sale_order_invoice = fields.Boolean(string="Invoice")
    mob_sale_order_shipment = fields.Boolean(string="Shipping")
    mob_sale_order_cancel = fields.Boolean(string="Cancel")

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_discount_product", self.mob_discount_product.id
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_coupon_product", self.mob_coupon_product.id
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_payment_term", self.mob_payment_term.id
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_sales_team", self.mob_sales_team.id
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_sales_person", self.mob_sales_person.id
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_sale_order_shipment", self.mob_sale_order_shipment
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_sale_order_cancel", self.mob_sale_order_cancel
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_sale_order_invoice", self.mob_sale_order_invoice
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
        OrderShip = IrConfigPrmtr.get_param('odoo_magento_connect.mob_sale_order_shipment')
        OrderInv = IrConfigPrmtr.get_param('odoo_magento_connect.mob_sale_order_invoice')
        OrderCanel = IrConfigPrmtr.get_param('odoo_magento_connect.mob_sale_order_cancel')
        DicsProd = int(IrConfigPrmtr.get_param('odoo_magento_connect.mob_discount_product'))
        CpnProd = int(IrConfigPrmtr.get_param('odoo_magento_connect.mob_coupon_product'))
        pymntTrm = int(IrConfigPrmtr.get_param('odoo_magento_connect.mob_payment_term'))
        salesTeam = int(IrConfigPrmtr.get_param('odoo_magento_connect.mob_sales_team'))
        SalesPrsn = int(IrConfigPrmtr.get_param('odoo_magento_connect.mob_sales_person'))
        res.update({
            'mob_sale_order_shipment' : OrderShip,
            'mob_sale_order_invoice' : OrderInv,
            'mob_sale_order_cancel' : OrderCanel,
            'mob_discount_product' : DicsProd,
            'mob_coupon_product' : CpnProd,
            'mob_payment_term' : pymntTrm,
            'mob_sales_team' : salesTeam,
            'mob_sales_person' : SalesPrsn,
        })
        return res
