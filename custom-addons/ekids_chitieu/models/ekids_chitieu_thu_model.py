from odoo import models, fields, api, _


class Chi(models.Model):
    _name = "ekids.chitieu_thu"
    _description = "Mô tả về chi tiêu của tổ chức"
    _order = "ngaychi asc"

    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one(
        'ekids.coso',
        string="Cơ sở",
        related='thang_id.coso_id',
        store=True,  # store=True để lưu xuống DB dùng cho filter/báo cáo
        ondelete="restrict",
    )
    thang_id = fields.Many2one('ekids.chitieu_thang', string='Tháng',required=True,ondelete="restrict")
    dm_loaichi_id = fields.Many2one('ekids.chitieu_dm_loaichi', string='Loại thu',required=True,ondelete="restrict")
    tien = fields.Float(string='Số tiền (vnđ)', digits=(10, 0),required=True)
    desc = fields.Html(string='Ghi chú')
    ngaychi = fields.Date(string="Ngày",required=True)






