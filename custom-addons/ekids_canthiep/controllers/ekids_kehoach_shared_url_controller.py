from odoo import http
from odoo.http import request

class KeHoachSharedURLController(http.Controller):

    @http.route('/kehoach/<string:type>/<string:token>', type='http', auth='public')
    def share_report(self,type, token, **kw):
        record = request.env['ekids.kehoach'].sudo().search([('access_token', '=', token)], limit=1)
        if not record:
            return request.not_found()

        try:
            if type=='0':
                report = request.env.ref('ekids_canthiep.in_kehoach_cho_giaovien_gon_action')



                # Odoo 18: _render(report_ref, res_ids, data)
                html, _ = report.sudo()._render(
                    'ekids_canthiep.in_kehoach_cho_giaovien_gon_action',
                    [record.id],
                    data=None
                )

                return request.make_response(html, headers=[('Content-Type', 'text/html')])
            else:

                report = request.env.ref('ekids_canthiep.in_kehoach_cho_giaovien_action')

                # Odoo 18: _render(report_ref, res_ids, data)
                html, _ = report.sudo()._render(
                    'ekids_canthiep.in_kehoach_cho_giaovien_action',
                    [record.id],
                    data=None
                )

                return request.make_response(html, headers=[('Content-Type', 'text/html')])


        except Exception as e:
            return request.make_response(
                f"<h2 style='color:red'>Error rendering report: {str(e)}</h2>",
                headers=[('Content-Type', 'text/html')]
            )