# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   "License URL : <https://store.webkul.com/license.html/>"
#
##########################################################################

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class OnboardingController(http.Controller):

    @http.route('/odoo_magento_connect/magento_bridge_dashboard_onboarding', auth='user', type='json')
    def magento_bridge_dashboard_onboarding(self):
        connectInfo = request.env['mob.dashboard'].get_connection_info()
        return {
            'html': request.env.ref('odoo_magento_connect.magento_bridge_dashboard_onboarding_panel').render({
                'connrecs': connectInfo})
        }
