from odoo import models, fields, api, exceptions


class LinhVuc(models.Model):
    _name = "ekids.ct_linhvuc"
    _description = "Lĩnh vực"

    sequence = fields.Integer(string="STT", default=1)
    ma = fields.Char(string="Mã")
    ten = fields.Char(string="Tên")
    name = fields.Char(string="Tên hiển thị", compute="_compute_ct_linhvuc_name", readonly=True)
    desc =fields.Html(string="Mô tả")
    chuongtrinh_id = fields.Many2one('ekids.ct_chuongtrinh', string='Chương trình')

    muctieu_ids = fields.One2many("ekids.ct_muctieu",
                              "linhvuc_id", string="Mục tiêu")

    tong_muctieu = fields.Integer(string="Tổng mục tiêu", compute="_compute_ct_linhvuc_tong_muctieu", store=False)


    def _compute_ct_linhvuc_tong_muctieu(self):
        for lv in self:
            count = self.env['ekids.ct_muctieu'].search_count([('linhvuc_id','=',lv.id)])
            if count:
                lv.tong_muctieu =count
            else:
                lv.tong_muctieu = 0
    def _compute_ct_linhvuc_name(self):
        for kh in self:
            if kh.ma:
                kh.name = '[' + kh.ma + ']-'
            if kh.ten:
                kh.name += kh.ten

    def action_view_ekid_canthiep_kanban_muctieu(self):
        return {
            'type': 'ir.actions.act_window',
            'name': self.ma,
            'res_model': 'ekids.ct_muctieu',
            'view_mode': 'list,kanban,form',
            'target': 'current',
            'domain': [('linhvuc_id', '=', self.id)],
            'context': {
                'default_chuongtrinh_id': self.chuongtrinh_id.id,
                'default_linhvuc_id': self.id,
            }

        }

