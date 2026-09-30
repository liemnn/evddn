from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class GiaoVienHocTapCongTac(models.Model):
    _name = "ekids.giaovien_hoctapcongtac"
    _description = "Quá trình học tập công tác"


    sequence = fields.Integer(string="Thứ tự", default=1)
    giaovien_id = fields.Many2one('ekids.giaovien', string="Giáo viên",required=True)
    tu_ngay = fields.Date(string="Nghỉ từ ngày", required=True)
    den_ngay = fields.Date(string="Nghỉ đến ngày")
    name = fields.Char(string="Nơi học tập/làm việc",required=True)
    chucvu = fields.Char(string="Bằng cấp/Chức vụ", required=True)
    thanhtich = fields.Char(string="Thành tích đạt được (nếu có)")
    is_tham_nien_duoccong = fields.Boolean(string="Thâm niên được tính",default=False)
    tham_nien = fields.Float(string="Thâm niên làm việc", digits=(10, 1),compute="_compute_tham_nien")


    @api.depends('tu_ngay', 'den_ngay', 'is_tham_nien_duoccong')
    def _compute_tham_nien(self):
        for record in self:
            if record.tu_ngay and record.is_tham_nien_duoccong:
                # Xác định ngày kết thúc: nếu có den_ngay thì dùng, nếu không thì lấy ngày hiện tại
                end_date = record.den_ngay if record.den_ngay else fields.Date.today()

                if end_date >= record.tu_ngay:
                    # Tính tổng số ngày chênh lệch
                    delta = end_date - record.tu_ngay
                    # Quy đổi ra năm (lấy số ngày chia cho 365.25 để tính cả năm nhuận)
                    so_nam = delta.days / 365.25
                    # Làm tròn đến 1 chữ số thập phân
                    record.tham_nien = round(so_nam, 1)
                else:
                    record.tham_nien = 0.0
            else:
                record.tham_nien = 0.0



