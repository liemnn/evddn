from odoo import http
from odoo.http import request

class HomeOverride(http.Controller):
    @http.route('/web/session/home', type='json', auth="user")
    def home_action(self):
        """Override home action: trả về None => đứng ở màn hình Apps/Home"""
        return None

