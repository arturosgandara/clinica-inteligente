# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################


from odoo import api, fields, models
from odoo.exceptions import UserError


Carrier_Code = [
    ('custom', 'Custom Value'),
    ('dhl', 'DHL (Deprecated)'),
    ('fedex', 'Federal Express'),
    ('ups', 'United Parcel Service'),
    ('usps', 'United States Postal Service'),
    ('dhlint', 'DHL')
]


class StockPicking(models.Model):
    _inherit = "stock.picking"

    carrier_code = fields.Selection(
        Carrier_Code,
        string='Magento Carrier',
        default="custom",
        help="Magento Carrier")
    magento_shipment = fields.Char(
        string='Magento Shipment',
        help="Contains Magento Order Shipment Number (eg. 300000008)")

    @api.multi
    def action_done(self):
        ctx = dict(self._context or {})
        res = super(StockPicking, self).action_done()
        if 'magento' not in ctx:
            self.mob_shipment()
        return res

    @api.multi
    def mob_shipment(self):
        context = dict(self._context or {})
        for pickingObj in self:
            orderObj = pickingObj.sale_id
            origin = pickingObj.origin
            if origin == orderObj.name:
                enableOrderShipment = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_magento_connect.mob_sale_order_shipment')
                if orderObj.ecommerce_channel == "magento" and enableOrderShipment:
                    itemData = {}
                    for moveLine in pickingObj.move_line_ids:
                        productSku = moveLine.product_id.default_code or False
                        if productSku :
                            quantity = moveLine.qty_done
                            itemData[productSku] = int(quantity)
                    context.update(itemData=itemData)
                    mageShipment = orderObj.with_context(context).manual_magento_order_operation(
                        "shipment")
                    if mageShipment and mageShipment[0]:
                        pickingObj.magento_shipment = mageShipment[0]
                        if pickingObj.carrier_tracking_ref:
                            pickingObj.action_sync_tracking_no()

    @api.multi
    def action_sync_tracking_no(self):
        text = ''
        ctx = dict(self._context or {})
        for pickingObj in self:
            saleId = pickingObj.sale_id.id
            mageShipment = pickingObj.magento_shipment
            carrierCode = pickingObj.carrier_code
            carrierTrackingNo = pickingObj.carrier_tracking_ref
            if not carrierTrackingNo:
                raise UserError(
                    'Warning! Sorry No Carrier Tracking No. Found!!!')
            elif not carrierCode:
                raise UserError('Warning! Please Select Magento Carrier!!!')
            carrierTitle = dict(Carrier_Code)[carrierCode]
            mapObj = self.env['wk.order.mapping'].search(
                [('erp_order_id', '=', saleId)], limit=1)
            if mapObj:
                magOrderId = mapObj.ecommerce_order_id
                ctx['instance_id'] = mapObj.instance_id.id
                shipTrackData = {
                    "entity": {
                        "orderId": magOrderId,
                        "parentId": mageShipment,
                        "trackNumber": carrierTrackingNo,
                        "title": carrierTitle,
                        "carrierCode": carrierCode
                    }
                }
                shipTrackResponse = self.env['magento.synchronization'].with_context(
                    ctx).callMagentoApi(
                    url='/V1/shipment/track',
                    method='post',
                    data=shipTrackData
                )
                if shipTrackResponse:
                    text = 'Tracking number successfully added.'
                else:
                    text = "Error While Syncing Tracking Info At Magento."
                return self.env['magento.synchronization'].display_message(
                    text)
# END
