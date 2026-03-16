from odoo import models, fields, api, exceptions


class DanhMucRoiLoan(models.Model):
    _name = "ekids.ct_dm_capdo"
    _description = "Dạng rồi loạn"

    chuongtrinh_id = fields.Many2one('ekids.ct_chuongtrinh', string='Chương trình')
    ma = fields.Char(string="Mã")
    ten = fields.Char(string="Tên")
    name = fields.Char(string="Tên hiển thị", compute="_compute_ct_dm_capdo_name", readonly=True)
    desc =fields.Html(string="Mô tả")

    muctieu_ids = fields.One2many("ekids.ct_muctieu",
                                  "dm_capdo_id", string="Mục tiêu")

    tong_muctieu = fields.Integer(string="Tổng mục tiêu", compute="_compute_ct_dm_capdo_tong_muctieu", store=False)



    def _compute_ct_dm_capdo_tong_muctieu(self):
        for record in self:
            count = self.env['ekids.ct_muctieu'].search_count([('dm_capdo_id','=',record.id)])
            if count:
                record.tong_muctieu =count
            else:
                record.tong_muctieu = 0

    def _compute_ct_dm_capdo_name(self):
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
            'domain': [('dm_capdo_id', '=', self.id)],
            'context': {
                'default_chuongtrinh_id': self.chuongtrinh_id.id,

            }

        }



