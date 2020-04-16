# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import fields, models


class MagentoRegion(models.Model):
    _name = "magento.region"
    _order = 'id desc'
    _description = "Magento Region"

    name = fields.Char(string='Region Name', size=100)
    mag_region_id = fields.Integer(string='Magento Region Id')
    country_code = fields.Char(string='Country Code', size=10)
    region_code = fields.Char(string='Region Code', size=10)
    created_by = fields.Char(string='Created By', default="odoo", size=64)
    create_date = fields.Datetime(string='Created Date')
    write_date = fields.Datetime(string='Updated Date')
