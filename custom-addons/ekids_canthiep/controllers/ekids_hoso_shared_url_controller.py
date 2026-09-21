from odoo import http
from odoo.http import request

class HoSoSharedURLController(http.Controller):

    @http.route(['/hocsinh/hosocanthiep/<string:token>'], type='http', auth='public', website=True)
    def view_hosocanthiep_by_token(self, token, **kwargs):
        hocsinh = request.env['ekids.hocsinh'].sudo().search([('access_token', '=', token)], limit=1)
        if not hocsinh:
            return request.not_found()

        # Render trực tiếp template hồ sơ can thiệp
        qcontext = {
            'docs': hocsinh,
        }
        return request.render('ekids_canthiep.kehoach_hoso_template', qcontext)