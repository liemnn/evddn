from odoo import api, fields, models
from datetime import datetime


class ThongBao(models.Model):
    _name = 'ekids.thongbao'
    _description = 'Thông báo từ Nhà trường'
    _order = 'tu_ngay desc'

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")

    name = fields.Char(string="Tiêu đề thông báo", required=True)
    tu_ngay = fields.Date(
        string="Thông báo từ ngày",
        required=True,
        default=fields.Date.context_today
    )
    den_ngay = fields.Date(
        string="Thông báo đến ngày",
        required=True,
        default=fields.Date.context_today
    )

    trangthai = fields.Selection([
        ('0', 'Đang soạn thảo'),
        ('1', 'Đã gửi đến phụ huynh')
    ], string="Trạng thái", default='0', index=True)

    def action_gui_thongbao(self):
        """Chuyển từ Đang soạn (0) sang Đã gửi (1)"""
        for rec in self:
            if rec.trangthai == '0':
                rec.write({'trangthai': '1'})
        return True

    def action_thu_hoi_thongbao(self):
        """Thu hồi: Chuyển từ Đã gửi (1) về Đang soạn (0)"""
        for rec in self:
            if rec.trangthai == '1':
                rec.write({'trangthai': '0'})
        return True


