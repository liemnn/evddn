from odoo import models, fields, api, _

from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError
import calendar


class DiemDanhCa2NgayWizard(models.TransientModel):
    _name = 'ekids.diemdanh_ca2ngay_wizard'
    _description = 'Chọn ngày điểm danh'

    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")

    hocphi_dm_ca_id = fields.Many2one("ekids.hocphi_dm_ca", required=True,
                                      string="Loại hình Ca/dịch vụ", index=True, ondelete="cascade")

    ngay = fields.Date(string="Ngày điểm danh", required=True)

    tu = fields.Char(string="Từ (HH:MM)", help='Format: HH:MM')
    den = fields.Char(string="Đến (HH:MM)", help='Format: HH:MM')

    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh", required=True, ondelete="restrict", index=True)
    giaovien_id = fields.Many2one("ekids.giaovien", string="Giáo viên thực hiện", required=True, ondelete="restrict",
                                  index=True)
    is_diemdanh_hocsinh =fields.Boolean(string="Là học sinh")
    loai = fields.Selection([
        ("4", "Học bù"),
        ("5", "Học tăng cường(được tính tiền tháng tới)"),

    ], string="Loại", required=True, default="4")

    trangthai = fields.Selection([
        ("0", "Đợi xác thực"),
        ("1", "Đã được học"),
        ("-1", "Không học"),
        ("2", "Nghỉ - Hoàn trả học phí"),
        ("3", "Nghỉ - Sẽ sắp lịch dạy bù"),
        ("4", "Đã dạy bù"),
    ], string="Xác nhận", required=True, default="1")

    desc = fields.Char(string="Mô tả")
    def action_tao_diemdanh_ca2ngay_hocbu(self):
        context =self.env.context
        is_nguoitao = context.get('is_nguoitao')
        is_diemdanh_hocsinh = context.get('is_diemdanh_hocsinh')

        for record in self:


            data ={
                'giaovien_id':record.giaovien_id.id,
                'hocsinh_id':record.hocsinh_id.id,
                'hocphi_dm_ca_id': record.hocphi_dm_ca_id.id,
                'ngay': record.ngay,
                'tu': record.tu,
                'den': record.den,
                'desc':record.desc,
                'trangthai': record.loai,
            }
            ca2ngay=self.env['ekids.diemdanh_ca2ngay'].create(data)

            if is_nguoitao == '0':
                if not is_diemdanh_hocsinh:
                    return ca2ngay.func_chamcong_giaovien_get_url_back()
                elif is_diemdanh_hocsinh == True:
                    return ca2ngay.func_diemdanh_hocsinh_get_url_back()



