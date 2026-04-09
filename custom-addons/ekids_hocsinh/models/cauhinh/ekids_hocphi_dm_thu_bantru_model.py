from odoo import api, fields, models
from datetime import datetime
import calendar
from odoo.exceptions import UserError

class DanhMucThuBanTru(models.Model):
    _name = 'ekids.hocphi_dm_thu_bantru'
    _description = 'Danh mục học phí của học sinh'
    _order = "sequence asc"

    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")
    name = fields.Char(string="Tên Loại thu",required=True)
    loai = fields.Selection([("0", "Thu cố định theo tháng")
                                     ,("1", "Khoản thu = Số tiền * Ngày đi học thực tế")
                                     ,("2", "Khoản thu = (Số tiền/Ngày đi học quy định của tháng) * Ngày đi học thực tế")
                                     ,("3", "Khoản thu = Công thực tự tính")
                                    ],string= "Loại hình thu"
                            ,default="1", required=True)
    is_formula = fields.Boolean(compute="_compute_is_formula")
    desc = fields.Char(string="Mô tả")
    tien = fields.Float(string='Số tiền(vnđ)', digits=(10, 0),required=True)
    is_hoantien_khi_nghi = fields.Boolean(string="Sẽ [Hoàn tiền] theo quy định khi [Nghỉ]", default=True)

    is_giam_hocphi = fields.Boolean(string="Được tính toán giảm [học phí] (nếu có)", default=True)

    trangthai = fields.Selection([("0", "Không hoạt động")
                                     , ("1", "Đang hoạt động")],default="1",required=True)
    is_apdung_rieng = fields.Boolean(string="Xem danh sách [Học sinh] đang áp dụng", default=False)


    hocsinh_ids = fields.Many2many(comodel_name="ekids.hocsinh"
                                      , relation="ekids_hocsinh2dm_thu_bantru_rel"
                                      , column1="dm_thu_bantru_id"
                                      , column2="hocsinh_id"
                                      , string="Khoản thu bán trú của học sinh")

    is_hocphi = fields.Boolean(string="Là khoản thu phục vụ học tập", default=False)

    @api.depends("loai")
    def _compute_is_formula(self):

        for record in self:
            if record.loai =='3':
                record.is_formula =True
            else:
                record.is_formula = False

    def func_taomoi_thu_bantru_cho_hocsinh(self,hocsinh,dm,is_ganthucong):
        data = {
            "coso_id": hocsinh.coso_id.id,
            "hocsinh_id": hocsinh.id,
            "dm_thu_bantru_id": dm.id,
            "tien":dm.tien,
            "desc" :dm.desc,
            "loai":dm.loai,
            "is_ganthucong":is_ganthucong
        }
        self.env['ekids.hocsinh_thu_bantru'].create(data)


    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=50, order=None):
        # Lấy thông tin người dùng hiện tại
        user = self.env.user
        context = self.env.context
        if context.get('default_coso_id'):
            domain += [('coso_id', '=', context.get('default_coso_id'))]  # Thêm điều kiện cho
        else:
            domain += [('coso_id', '=',-1)]  # Thêm điều kiện cho
        return super().search_fetch(domain, field_names, offset, limit, order)



