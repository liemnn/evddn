from odoo import http
from odoo.http import request


class InfoController(http.Controller):

    @http.route('/ph/info', type='http', auth='public', website=True)
    def coming_soon_page(self, **kwargs):
        # Trỏ tới ID của template XML bên dưới
        return request.render('ekids_phuhuynh.coming_soon_page', {})