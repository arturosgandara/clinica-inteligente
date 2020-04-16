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

from odoo import api, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _get_ecommerces(self):
        res = super(SaleOrder, self)._get_ecommerces()
        res.append(('magento', 'Magento'))
        return res

    @api.multi
    def action_cancel(self):
        ctx = dict(self._context or {})
        res = super(SaleOrder, self).action_cancel()
        enableOrderCancel = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_magento_connect.mob_sale_order_cancel'
        )
        if not enableOrderCancel or 'magento' in ctx:
            return res
        for saleObj in self:
            if saleObj.ecommerce_channel == "magento" and enableOrderCancel:
                saleObj.manual_magento_order_operation("cancel")
        return res

    @api.one
    def manual_magento_order_operation(self, opr):
        text = ''
        status = 'no'
        session = False
        mageShipment = False
        ctx = dict(self._context or {})
        OrderMapObj = self.env['wk.order.mapping'].search(
            [('erp_order_id', '=', self.id)], limit=1)
        if OrderMapObj:
            incrementId = OrderMapObj.name
            orderName = self.name
            connectionObj = OrderMapObj.instance_id
            ctx['instance_id'] = connectionObj.id
            if connectionObj.active:
                if connectionObj.state != 'enable':
                    return False
                else:
                    connection = self.env[
                        'magento.configure'].with_context(ctx)._create_connection()
                    if connection:
                        url = connection[0]
                        token = connection[1]
                        apiOpr = ''
                        if token and incrementId:
                            if opr == "shipment":
                                apiOpr = 'OrderShipment'
                            elif opr == "cancel":
                                apiOpr = 'OrderCancel'
                            elif opr == "invoice":
                                apiOpr = 'OrderInvoice'
                        if apiOpr:
                            OrderData = {'orderId': incrementId}
                            itemData = self._context.get('itemData')
                            if itemData :
                                OrderData.update(itemData=itemData)
                            apiResponse = self.env['magento.synchronization'].with_context(ctx).callMagentoApi(
                                baseUrl=url,
                                url='/V1/odoomagentoconnect/' + apiOpr,
                                method='post',
                                token=token,
                                data=OrderData
                            )
                            if apiResponse:
                                if apiOpr == "OrderShipment":
                                    mageShipment = apiResponse
                                text = '%s of order %s has been successfully updated on magento.' % (opr, orderName)
                                status = 'yes'
                            else:
                                text = 'Magento %s Error For Order %s , Error' % (opr, orderName)
                                status = 'no'
                    else:
                        text = 'Magento %s Error For Order %s >> Could not able to connect Magento.' % (opr, orderName)
                self._cr.commit()
                self.env['magento.sync.history'].create(
                    {'status': status, 'action_on': 'order', 'action': 'b', 'error_message': text})
        return mageShipment
