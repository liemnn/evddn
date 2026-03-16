from odoo import models, fields, api, _


class Chi(models.Model):
    _name = "ekids.chitieu_chi"
    _description = "Mô tả về chi tiêu của tổ chức"
    _order = "ngaychi asc"

    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True,ondelete="restrict")
    thang_id = fields.Many2one('ekids.chitieu_thang', string='Tháng',required=True,ondelete="restrict")
    dm_loaichi_id = fields.Many2one('ekids.chitieu_dm_loaichi', string='Loại chi',required=True,ondelete="restrict")
    tien = fields.Float(string='Số tiền (vnđ)', digits=(10, 0),required=True)
    desc = fields.Html(string='Ghi chú')
    ngaychi = fields.Date(string="Ngày",required=True)






