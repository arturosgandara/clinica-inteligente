# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
##########################################################################

{
    'name': 'Odoo: Bridge Skeleton',
    'version': '2.0.0',
    'category': 'Bridge Module',
    'author': 'Webkul Software Pvt. Ltd.',
    'website': 'https://store.webkul.com/Magento-OpenERP-Bridge.html',
    'summary': 'Core of Webkul Bridge Modules',
    'description': """
        This is core for all basic operations features provided in Webkul's Bridge Modules.
    """,
    'images': [],
    'depends': [
        'sale',
        'stock',
        'account',
        'account_cancel',
        'delivery'
    ],
    'data': [
        'views/sale_views.xml',
        'views/res_partner_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_check',
}
