# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, models


class WkSkeleton(models.TransientModel):
    _inherit = "wk.skeleton"

    @api.model
    def set_order_shipped(self, orderId):
        """Ship the order in Odoo via requests from XML-RPC
        @param order_id: Odoo Order ID
        @param context: Mandatory Dictionary with key 'ecommerce' to identify the request from E-Commerce
        @return:  A dictionary of status and status message of transaction"""
        ctx = dict(self._context or {})
        status = True
        status_message = "Order Successfully Shipped."
        try:
            saleObj = self.env['sale.order'].browse(orderId)
            backOrderModel = self.env['stock.backorder.confirmation']
            if saleObj.state == 'draft':
                self.confirm_odoo_order([orderId])
            if saleObj.picking_ids:
                self.turn_odoo_connection_off()
                for pickingObj in saleObj.picking_ids.filtered(
                        lambda pickingObj: pickingObj.picking_type_code == 'outgoing' and pickingObj.state != 'done'):
                    backorder = False
                    ctx['active_id'] = pickingObj.id
                    ctx['picking_id'] = pickingObj.id
                    pickingObj.action_assign()
                    for packObj in pickingObj.move_line_ids:
                        if packObj.qty_done and packObj.qty_done < packObj.product_qty:
                            backorder = True
                            continue
                        elif packObj.product_qty > 0:
                            packObj.write({'qty_done': packObj.product_qty})
                        else:
                            packObj.unlink()
                    if backorder:
                        backorderObj = backOrderModel.create(
                            {'pick_ids': [(4, pickingObj.id)]})
                        backorderObj.process_cancel_backorder()
                    else:
                        pickingObj.button_validate()
                    self.with_context(ctx).set_extra_values()
        except Exception as e:
            status = False
            status_message = "Error in Delivering Order: %s" % str(e)
        finally:
            self.turn_odoo_connection_on()
            return {
                'status_message': status_message,
                'status': status
            }
