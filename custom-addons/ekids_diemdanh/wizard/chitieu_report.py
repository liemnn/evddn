from odoo import fields, models, api, _


class ChiTieuReportWizard(models.TransientModel):
    _name = 'chitieu.report.wizard'
    _description = 'Báo cáo chi tiêu năm'


    coso_id = fields.Many2one('ekids.coso', string='Cơ sở')
    nam_id = fields.Many2one('ekids.chitieu_nam', string='Năm')
    tong_chitieu = fields.Integer(string='Tổng Chi Tiêu', readonly=True)


    @api.model
    def default_get(self, fields):
        res = super(ChiTieuReportWizard, self).default_get(fields)
        nam_id = self.env.context.get('active_id')
        nam_record = self.env['ekids.chitieu_nam'].browse(nam_id)
        res.update({
            'coso_id': nam_record.coso_id.id,
            'nam_id': nam_id,
            'tong_chitieu': nam_record.tong,
        })
        return res

    # def action_export_report(self):
    #     # Implement your logic to export the report to a file here
    #     pass

