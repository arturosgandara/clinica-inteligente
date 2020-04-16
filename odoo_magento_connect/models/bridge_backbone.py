# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import _, api, models


class BridgeBackbone(models.TransientModel):
    _name = "bridge.backbone"

    @api.model
    def create_pricelist(self, data):
        """create and search pricelist by any webservice like xmlrpc.
        @param code: currency code.
        @return: pricelist_id
        """
        currencyObj = self.env['res.currency'].search(
            [('name', '=', data['code'])], limit=1)
        priceListModel = self.env['product.pricelist']
        if currencyObj:
            pricelistObj = priceListModel.search(
                [('currency_id', '=', currencyObj.id)], limit=1)
            if not pricelistObj:
                pricelistDict = {
                    'name' : 'Mage_' + data['code'],
                    'active' : True,
                    'currency_id' : currencyObj.id
                }
                pricelistObj = priceListModel.create(pricelistDict)
                return pricelistObj.id
            else:
                return pricelistObj.id
        return 0

    @api.model
    def _get_journal_code(self, name, sep=' '):
        nameSepList = []
        for nampSplit in name.split(sep):
            if nampSplit:
                nameSeprtd = nampSplit.title()[0]
                if nameSeprtd.isalnum():
                    nameSepList.append(nameSeprtd)
        code = ''.join(nameSepList)
        code = code[0:3]
        journalModel = self.env['account.journal']
        existObj = journalModel.search([('code', '=', code)])
        if existObj:
            for i in range(1, 200):
                existObj = journalModel.search(
                    [('code', '=', code + str(i))])
                if not existObj:
                    return (code + str(i))[-5:]
        return code

    @api.model
    def create_payment_method(self, data):
        """create Journal by any webservice like xmlrpc.
        @param name: journal name.
        @return: payment_id
        """
        paymentId = 0
        journalModel = self.env['account.journal']
        res = journalModel.search(
            [('type', '=', 'cash')], limit=1)
        if res:
            data['default_credit_account_id'] = res[
                0].default_credit_account_id.id
            data['default_debit_account_id'] = res[
                0].default_debit_account_id.id
            data['code'] = self._get_journal_code(data.get('name'), ' ')
            paymentObj = journalModel.create(data)
            paymentId = paymentObj.id
        return paymentId

    # code for update an inventry of a product......

    @api.model
    def update_quantity(self, data):
        """ Changes the Product Quantity by making a Physical Inventory.
        @param self: The object pointer.
        @param data: List of product_id and new_quantity
        @return: True
        """

        locationId = 0
        productId = data.get('product_id')
        mageProdQty = int(data.get('new_quantity'))
        ctx = dict(self._context or {})
        ctx['stock_from'] = 'magento'
        assert productId, _('Active ID is not set in Context')
        if 'instance_id' in ctx:
            stockChangeModel = self.env['stock.change.product.qty']
            instanceId = ctx.get('instance_id')
            connectionObj = self.env['magento.configure'].browse(
                ctx.get('instance_id'))
            if connectionObj.active:
                locationId = connectionObj.warehouse_id.lot_stock_id.id
            else:
                locationObjs = self.env['stock.warehouse'].search([])
                if locationObjs:
                    locationId = locationObjs[0].lot_stock_id.id
            updtQtyDict = {
                'product_id' : productId,
                'location_id' : locationId,
                'new_quantity' : mageProdQty,
            }
            entityObj = stockChangeModel.with_context(ctx).create(updtQtyDict)
            entityObj.change_product_qty()
            return True
        return False

# END
