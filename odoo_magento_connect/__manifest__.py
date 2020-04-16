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
    'name': 'Magento Odoo Bridge',
    'version': '2.0.0',
    'category': 'Generic Modules',
    'author': 'Webkul Software Pvt. Ltd.',
    'website': 'https://store.webkul.com/Magento-2/Odoo-Bridge-For-Magento2.html',
    'sequence': 1,
    'summary': 'Basic MOB',
    'description': """

Magento Odoo Bridge (MOB)
=========================

This Brilliant Module will Connect Odoo with Magento and synchronise Data.
--------------------------------------------------------------------------


Some of the brilliant feature of the module:
--------------------------------------------

	1. synchronise all the catalog categories to Magento.

	2. synchronise all the catalog products to Magento.

	3. synchronise all the Attributes and Values.

	4. synchronise all the order(Invoice, shipping) Status to Magento.

	5. Import Magento Regions.

	6. synchronise inventory of catelog products.

This module works very well with latest version of magento 2.* and Odoo 12.0
------------------------------------------------------------------------------
    """,
    'depends': [
        'bridge_skeleton',
        'variant_price_extra',
    ],
    'data': [
        'wizard/magento_wizard_view.xml',
        'security/bridge_security.xml',
        'security/ir.model.access.csv',
        'wizard/message_wizard_view.xml',
        'wizard/status_wizard_view.xml',
        'wizard/synchronization_wizard_view.xml',
        'data/mob_server_actions.xml',
        'views/product_views.xml',
        'views/product_template_views.xml',
        'views/stock_picking_views.xml',
        'views/mob_configure_view.xml',
        'views/mob_synchronization_view.xml',
        'views/mob_region_view.xml',
        'views/mob_attribute_set_view.xml',
        'views/mob_product_attribute_view.xml',
        'views/mob_product_attribute_value_view.xml',
        'views/mob_category_view.xml',
        'views/mob_product_template_view.xml',
        'views/mob_product_view.xml',
        'views/mob_partner_view.xml',
        'views/mob_order_view.xml',
        'views/mob_synchronization_history_view.xml',
        'views/res_config_view.xml',
        'views/mob_sequence.xml',
        'views/magento_bridge_templates.xml',
        'views/dashboard_extend_view.xml',
        'views/mob_dashboard_view.xml',
        'views/mob_menus.xml',
        'data/mob_data.xml',
    ],

    'application': True,
    'installable': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_check',
}
