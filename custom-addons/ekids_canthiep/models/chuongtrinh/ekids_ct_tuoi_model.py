from odoo import models, fields, api, exceptions


class DanhMucTuoi(models.Model):
    _name = "ekids.ct_tuoi"
    _description = "Tuổi thực tế"
    _order = "sequence asc"

    coso_id = fields.Many2one("ekids.coso", related="chuongtrinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    sequence = fields.Integer(string="STT", default=1)
    index= fields.Integer(string="STT", compute="_compute_index", store=False)

    chuongtrinh_id = fields.Many2one('ekids.ct_chuongtrinh', string='Chương trình')
    name = fields.Char(string="Tên",required=True)
    desc =fields.Html(string="Mô tả")

    tong_muctieu = fields.Integer(string="Tổng mục tiêu", compute="_compute_tong_muctieu", store=False)

    def _compute_index(self):
        index = 1
        for record in self:
            record.index = index
            index += 1

    def _compute_tong_muctieu(self):
        for tuoi in self:
            count = self.env['ekids.ct_muctieu'].search_count([('tuoi_id', '=', tuoi.id)])
            if count:
                tuoi.tong_muctieu = count
            else:
                tuoi.tong_muctieu = 0

    def action_xem_muctieu(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "TUỔI:" + self.name,
            'res_model': 'ekids.ct_muctieu',
            'view_mode': 'list,kanban,form',
            'target': 'current',
            'domain': [('tuoi_id', '=', self.id)],
            'context': {
                'default_chuongtrinh_id': self.chuongtrinh_id.id,
                'default_tuoi_id': self.id,
            }

        }



