# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import fields, models


class MagentoSyncHistory(models.Model):
    _name = "magento.sync.history"
    _order = 'id desc'
    _description = "Magento Synchronization History"

    status = fields.Selection([
        ('yes', 'Successfull'),
        ('no', 'Un-Successfull')
    ], string='Status')
    action_on = fields.Selection([
        ('product', 'Product'),
        ('category', 'Category'),
        ('customer', 'Customer'),
        ('order', 'Order'),
        ('api', 'Synchronization')
    ], string='Action On')
    action = fields.Selection([
        ('a', 'Import'),
        ('b', 'Export'),
        ('c', 'Update')
    ], string='Action')
    create_date = fields.Datetime(string='Created Date')
    error_message = fields.Text(string='Summary')
