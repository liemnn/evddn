from odoo import http
from odoo.http import request

class PhieuLuongController(http.Controller):

    @http.route('/hocphi/<string:token>', type='http', auth='public')
    def share_report(self, token, **kw):
        record = request.env['ekids.hocphi'].sudo().search([('access_token', '=', token)], limit=1)
        if not record:
            return request.not_found()

        try:
            report = request.env.ref('ekids_hocsinh.action_phieuthus')

            # Odoo 18: _render(report_ref, res_ids, data)
            html, _ = report.sudo()._render(
                'ekids_hocsinh.action_phieuthus',
                [record.id],
                data=None
            )

            return request.make_response(html, headers=[('Content-Type', 'text/html')])

        except Exception as e:
            return request.make_response(
                f"<h2 style='color:red'>Error rendering report: {str(e)}</h2>",
                headers=[('Content-Type', 'text/html')]
            )