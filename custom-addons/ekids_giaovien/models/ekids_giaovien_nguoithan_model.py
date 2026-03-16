from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class GiaoVienNguoiThan(models.Model):
    _name = "ekids.giaovien_nguoithan"
    _description = "Đối tượng giáo viên của cơ sở"


    sequence = fields.Integer(string="Thứ tự", default=1)
    giaovien_id = fields.Many2one('ekids.giaovien', string="Giáo viên",required=True)
    name = fields.Char(string="Họ và tên",required=True)
    dienthoai = fields.Char(string="Điện thoại")
    gioitinh  = fields.Selection([("0","Nữ"),("1","Nam")],'Giới tính',required=True)
    ngaysinh = fields.Date(string="Ngày sinh")
    tuoi = fields.Char(string="Tuổi", compute="_compute_giaovien_nguoithan_tuoi")
    quanhe = fields.Selection([
                                ("0", "Cha/Mẹ"),
                                ("1", "Vợ/Chồng"),
                                ("2", "Con"),
                                ("3", "Khác"),
                                ], 'Quan hệ với giáo viên',required=True)

    @api.depends('ngaysinh')
    def _compute_giaovien_nguoithan_tuoi(self):
        now = datetime.today()
        for hs in self:
            if hs.ngaysinh:
                tong_thang = (now.year - hs.ngaysinh.year) * 12 + (now.month - hs.ngaysinh.month)
                if now.day < now.day:
                    tong_thang -= 1
                nam = tong_thang // 12
                thang = tong_thang % 12
                tuoi = ""
                if nam >= 1:
                    tuoi += str(nam) + " tuổi "
                if thang >= 1:
                    tuoi += str(thang) + " tháng"
                hs.tuoi = tuoi
            else:
                hs.tuoi = '0'

