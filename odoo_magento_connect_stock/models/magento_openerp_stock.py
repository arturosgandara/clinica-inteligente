# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from urllib.parse import quote

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def _stock_def_setting(self):
        configModel = self.env['res.config.settings']
        vals = {
            'mob_stock_action' : 'qoh'
            }
        defaultSetObj = configModel.create(vals)
        defaultSetObj.execute()
        return True


    @api.multi
    def _action_confirm(self, *args, **kwargs):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        """
        mobStockAction = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_magento_connect.mob_stock_action'
        )
        res = super(StockMove, self)._action_confirm(*args, **kwargs)
        if mobStockAction == "fq":
            ctx = dict(self._context or {})
            ctx['mob_stock_action_val'] = mobStockAction
            res.with_context(ctx).fetch_stock_warehouse()
        return res

    @api.multi
    def _action_cancel(self):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        """
        ctx = dict(self._context or {})
        ctx['action_cancel'] = True
        mobStockAction = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_magento_connect.mob_stock_action'
        )
        check = False
        for obj in self:
            if obj.state == "cancel":
                check = True
        res = super(StockMove, self)._action_cancel()
        if mobStockAction == "fq" and not check:
            ctx['mob_stock_action_val'] = mobStockAction
            self.with_context(ctx).fetch_stock_warehouse()
        return res

    @api.multi
    def _action_done(self):
        """ Process completly the moves given as ids and if all moves are done, it will finish the picking.
        """
        mobStockAction = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_magento_connect.mob_stock_action'
        )
        check = False
        for obj in self:
            if obj.location_id.usage == "inventory" or obj.location_dest_id.usage == "inventory":
                check = True
        res = super(StockMove, self)._action_done()
        if mobStockAction == "qoh" or check:
            ctx = dict(self._context or {})
            ctx['mob_stock_action_val'] = mobStockAction
            self.with_context(ctx).fetch_stock_warehouse()
        return res

    @api.multi
    def fetch_stock_warehouse(self):
        ctx = dict(self._context or {})
        productQuantity = 0
        connectionObj = self.env['magento.configure'].search([('active', '=', True)], limit=1)
        if 'stock_from' not in ctx and connectionObj:
            for data in self:
                odooProductId = data.product_id.id
                sku = data.product_id.default_code
                flag = 1
                if data.origin:
                    saleObjs = data.env['sale.order'].search(
                        [('name', '=', data.origin)])
                    if saleObjs:
                        get_channel = saleObjs[0].ecommerce_channel
                        if get_channel == 'magento' and data.picking_id \
                                and data.picking_id.picking_type_code == 'outgoing':
                            flag = 0
                else:
                    flag = 2  # no origin
                warehouseId = 0
                if flag == 1:
                    warehouseId = data.warehouse_id.id
                if flag == 2:
                    locationObj = data.location_dest_id
                    companyId = data.company_id.id
                    warehouseId = self.check_warehouse_location(
                        locationObj, companyId) # Receiving Goods
                    if not warehouseId :
                        locationObj = data.location_id
                        warehouseId = self.check_warehouse_location(
                            locationObj, companyId) # Sending Goods
                data.check_warehouse(
                    odooProductId, sku, warehouseId, productQuantity)
        return True

    @api.model
    def check_warehouse_location(self, locationObj, companyId):
        warehouseModel = self.env['stock.warehouse']
        while locationObj :
            warehouseObj = warehouseModel.search([
                ('lot_stock_id', '=', locationObj.id), 
                ('company_id', '=', companyId)
            ], limit=1)
            if warehouseObj :
                return warehouseObj.id
            locationObj = locationObj.location_id
        return False

    @api.model
    def check_warehouse(self, odooProductId, sku, warehouseId, productQuantity):
        ctx = dict(self._context or {})
        mappingObj = self.env['magento.product'].search(
            [('pro_name', '=', odooProductId)], limit=1)
        if mappingObj:
            instanceObj = mappingObj.instance_id
            mageProductId = mappingObj.mag_product_id
            stockItemId = mappingObj.magento_stock_id
            if mappingObj.instance_id.warehouse_id.id == warehouseId:
                ctx['warehouse'] = warehouseId
                productObj = self.env['product.product'].with_context(
                    ctx).browse(odooProductId)
                if ctx.get('mob_stock_action_val') == "qoh":
                    productQuantity = productObj.qty_available - productObj.outgoing_qty
                else:
                    productQuantity = productObj.virtual_available
                self.synch_quantity(
                    mageProductId, productQuantity, sku, stockItemId, instanceObj)
        return True

    @api.model
    def synch_quantity(self, mageProductId, productQuantity, sku, stockItemId, instanceObj):
        response = self.update_quantity(
            mageProductId, productQuantity, sku, stockItemId, instanceObj)
        if response[0] == 1:
            return True
        else:
            self.env['magento.sync.history'].create(
                {'status': 'no', 'action_on': 'product', 'action': 'c', 'error_message': response[1]})
            return False

    @api.model
    def update_quantity(self, mageProductId, productQuantity, sku, stockItemId, instanceObj):
        text = ''
        ctx = dict(self._context or {})
        ctx['instance_id'] = instanceObj.id
        try:
            sku = quote(sku, safe='')
        except Exception as e:
            sku = quote(sku.encode("utf-8"), safe='')
        if mageProductId:
            if not instanceObj.active:
                return [
                    0, ' Connection needs one Active Configuration setting.']
            else:
                try:
                    if type(productQuantity) == str:
                        productQuantity = productQuantity.split('.')[0]
                    if type(productQuantity) == float:
                        productQuantity = productQuantity.as_integer_ratio()[0]
                    stockData = {"stockItem": {
                        "itemId": stockItemId,
                        "productId": mageProductId,
                        "stockId": 1,
                        "qty": productQuantity,
                        "isInStock": True if productQuantity > 0 else False, 
                    }}
                    apiResponse = self.env['magento.synchronization'].callMagentoApi(
                        url='/V1/products/' + str(sku) + '/stockItems/' + str(stockItemId),
                        method='put',
                        data=stockData,
                    )
                    return [1, '']
                except Exception as e:
                    return [0, ' Error in Updating Quantity for Magneto Product Id %s, Reason >>%s' % (mageProductId,str(e))]
        else:
            return [0, 'Error in Updating Stock, Magento Product Id Not Found!!!']
