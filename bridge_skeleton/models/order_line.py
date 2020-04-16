# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, models


def _unescape(text):
    ##
    # Replaces all encoded characters by urlib with plain utf8 string.
    #
    # @param text source text.
    # @return The plain text.
    from urllib.parse import unquote_plus
    try:
        text = unquote_plus(text)
        return text
    except Exception as e:
        return text


class WkSkeleton(models.TransientModel):
    _inherit = "wk.skeleton"

    @api.model
    def create_order_shipping_and_voucher_line(self, orderLine):
        """ @params orderLine: A dictionary of sale ordre line fields
                @params context: a standard odoo Dictionary with context having keyword to check origin of fumction call and identify type of line for shipping and vaoucher
                @return : A dictionary with updated values of order line"""
        productId = self.get_default_virtual_product_id(orderLine)
        orderLine['product_id'] = productId
        if orderLine['name'].startswith('S'):
            orderLine['is_delivery'] = True
        orderLine.pop('ecommerce_channel', None)
        res = self.create_sale_order_line(orderLine)
        return res

    @api.model
    def get_default_virtual_product_id(self, orderLine):
        ecommerceChannel = orderLine['ecommerce_channel']
        if hasattr(self, 'get_%s_virtual_product_id' % ecommerceChannel):
            return getattr(
                self, 'get_%s_virtual_product_id' %
                ecommerceChannel)(orderLine)
        else:
            return False

    @api.model
    def create_sale_order_line(self, orderLineData):
        """Create Sale Order Lines from XML-RPC
        @param orderLineData: A List of dictionary of Sale Order line fields in which required field(s) are 'order_id', `product_uom_qty`, `price_unit`
                `product_id`: mandatory for non shipping/voucher order lines
        @return: A dictionary of Status, Order Line ID, Status Message  """
        ctx = dict(self._context or {})
        status = True
        orderLineId = False
        statusMessage = "Order Line Successfully Created."
        try:
            # To FIX:
            # Cannot call Onchange in sale order line
            productObj = self.env['product.product'].browse(
                orderLineData['product_id'])
            orderLineData.update({'product_uom': productObj.uom_id.id})
            name = orderLineData.get('name', None)
            description = orderLineData.pop('description', None)
            if description :
                orderLineData.update(name=_unescape(description))
            elif name:
                orderLineData.update(name=_unescape(name))
            else:
                orderLineData.update(
                    name=productObj.description_sale or productObj.name
                )
            orderLineId = self.env['sale.order.line'].create(orderLineData)
        except Exception as e:
            statusMessage = "Error in creating order Line on Odoo: %s" % str(e)
            status = False
        finally:
            returnDict = dict(
                order_line_id='',
                status=status,
                status_message=statusMessage,
            )
            if orderLineId:
                returnDict.update(
                    order_line_id=orderLineId.id
                )
            return returnDict
