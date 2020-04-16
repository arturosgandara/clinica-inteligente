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
    _name = "wk.skeleton"
    _description = " Skeleton for all XML RPC imports in Odoo"

    @api.model
    def turn_odoo_connection_off(self):
        """ To be inherited by bridge module for making connection Inactive on Odoo End"""
        return True

    @api.model
    def turn_odoo_connection_on(self):
        """ To be inherited by bridge module for making connection Active on Odoo End"""
        return True

    @api.model
    def set_extra_values(self):
        """ Add extra values"""
        return True
    # Order Status Updates

    @api.model
    def set_order_cancel(self, orderId):
        """Cancel the order in Odoo via requests from XML-RPC
                @param order_id: Odoo Order ID
                @param context: Mandatory Dictionary with key 'ecommerce' to identify the request from E-Commerce
                @return: A dictionary of status and status message of transaction"""
        ctx = dict(self._context or {})
        status = True
        statusMessage = "Order Successfully Cancelled."
        isVoucherInstalled = False
        try:
            saleObj = self.env['sale.order'].browse(orderId)
            statusMessage = "Odoo Order %s Cancelled Successfully." % (
                saleObj.name)
            self.turn_odoo_connection_off()
            if self.env['ir.module.module'].sudo().search(
                    [('name', '=', 'account_voucher')], limit=1).state == 'installed':
                isVoucherInstalled = True
                voucherModel = self.env['account.voucher']
            if saleObj.invoice_ids:
                for invoiceObj in saleObj.invoice_ids:
                    invoiceObj.journal_id.update_posted = True
                    if invoiceObj.state == "paid" and isVoucherInstalled:
                        for paymentObj in invoiceObj.payment_ids:
                            voucherObjs = voucherModel.search(
                                [('move_ids.name', '=', paymentObj.name)])
                            if voucherObjs:
                                for voucherObj in voucherObjs:
                                    voucherObj.journal_id.update_posted = True
                                    voucherObj.cancel_voucher()
                    invoiceObj.action_cancel()
            if saleObj.picking_ids:
                if 'done' in saleObj.picking_ids.mapped('state'):
                    donePickingNames = saleObj.picking_ids.filtered(
                        lambda pickingObj: pickingObj.state == 'done').mapped('name')
                    status = True
                    statusMessage = "Odoo Order %s Cancelled but transferred pickings can't cancelled," % (
                        saleObj.name) + " Please create return for pickings %s !!!" % (", ".join(donePickingNames))
            saleObj.with_context(ctx).action_cancel()
        except Exception as e:
            status = False
            statusMessage = "Odoo Order %s Not cancelled. Reason: %s" % (
                saleObj.name, str(e))
        finally:
            self.turn_odoo_connection_on()
            return {
                'status_message': statusMessage,
                'status': status
            }

    @api.model
    def get_default_configuration_data(self, ecommerceChannel):
        """@return: Return a dictionary of Sale Order keys by browsing the Configuration of Bridge Module Installed"""
        if hasattr(self, 'get_%s_configuration_data' % ecommerceChannel):
            return getattr(
                self, 'get_%s_configuration_data' %
                ecommerceChannel)()
        else:
            return False

    @api.model
    def create_order_mapping(self, mapData):
        """Create Mapping on Odoo end for newly created order
        @param order_id: Odoo Order ID
        @context : A dictionary consisting of e-commerce Order ID"""

        self.env['wk.order.mapping'].create(mapData)
        return True

    @api.model
    def create_order(self, saleData):
        """ Create Order on Odoo along with creating Mapping
        @param saleData: dictionary of Odoo sale.order model fields
        @param context: Standard dictionary with 'ecommerce' key to identify the origin of request and
                                        e-commerce order ID.
        @return: A dictionary with status, order_id, and status_message"""
        ctx = dict(self._context or {})
        # check saleData for min no of keys presen or not
        orderName, orderId, status, statusMessage = "", False, True, "Order Successfully Created."
        ecommerceChannel = saleData.get('ecommerce_channel')
        ecommerceOrderId = saleData.get('ecommerce_order_id')
        saleData.pop('ecommerce_order_id', None)
        configData = self.get_default_configuration_data(ecommerceChannel)
        saleData.update(configData)

        try:
            orderObj = self.env['sale.order'].create(saleData)
            orderId = orderObj.id
            orderName = orderObj.name

            mappingData = {
                'ecommerce_channel': ecommerceChannel,
                'erp_order_id': orderId,
                'ecommerce_order_id': ecommerceOrderId,
                'name': saleData['origin'],
            }
            self.create_order_mapping(mappingData)
        except Exception as e:
            statusMessage = "Error in creating order on Odoo: %s" % str(e)
            status = False
        finally:
            return {
                'order_id': orderId,
                'order_name': orderName,
                'status_message': statusMessage,
                'status': status
            }

    @api.model
    def confirm_odoo_order(self, orderId):
        """ Confirms Odoo Order from E-Commerce
        @param order_id: Odoo/ERP Sale Order ID
        @return: a dictionary of True or False based on Transaction Result with status_message"""
        #REMOVED this long as python3 not supported long  # if isinstance(orderId, (int, long)):
        if isinstance(orderId, (int)):
            orderId = [orderId]
        ctx = dict(self._context or {})
        status = True
        statusMessage = "Order Successfully Confirmed!!!"
        try:
            saleObj = self.env['sale.order'].browse(orderId)
            saleObj.action_confirm()
        except Exception as e:
            statusMessage = "Error in Confirming Order on Odoo: %s" % str(e)
            status = False
        finally:
            return {
                'status': status,
                'status_message': statusMessage
            }
