from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _  # <-- THÊM DÒNG NÀY
from .ekids_read_group_abstractmodel import ReadGroupAbstractModel
from datetime import datetime,date
class HocSinhLichSuCanThiep(models.Model,ReadGroupAbstractModel):
    _name = "ekids.hocsinh_lichsu_canthiep"
    _description = "Lịch sử can thiệp của trẻ"
    _order = "tu_ngay desc"

    sequence = fields.Integer(string="TT", default=1)
    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    hocsinh_id = fields.Many2one('ekids.hocsinh', string="Học sinh", required=True)
    tu_ngay = fields.Date(string="Từ ngày", required=True)
    den_ngay = fields.Date(string="Đến ngày")
    thoigian_hoc = fields.Char(string="Thời gian theo học", compute="_compute_thoigian_hoc", store=False)

    name = fields.Char(string="Nơi học tập/can thiệp", required=True)
    desc = fields.Char(string="Ghi chú")
    trangthai = fields.Selection([
        ("1", "Đang theo học"),
        ("-1", "Đã nghỉ"),

    ]
        , string="Trạng thái", default="-1", required=True)

    @api.depends('tu_ngay', 'den_ngay', 'trangthai')
    def _compute_thoigian_hoc(self):
        today = fields.Date.today()
        for rec in self:
            if not rec.tu_ngay:
                rec.thoigian_hoc = "Chưa có"
                continue

            # Xác định ngày kết thúc: Nếu đã nghỉ hoặc có đến ngày thì dùng den_ngay, nếu đang học thì tính đến hôm nay
            if rec.trangthai == "-1":
                end_date = rec.den_ngay if rec.den_ngay else today
            else:
                end_date = today

            if end_date < rec.tu_ngay:
                rec.thoigian_hoc = "Không hợp lệ"
                continue

            # Tính số ngày chênh lệch
            tong_ngay = (end_date - rec.tu_ngay).days

            if tong_ngay <= 0:
                rec.thoigian_hoc = "Dưới 1 ngày"
            else:
                # Quy đổi tương đối ra tháng (1 tháng = 30 ngày)
                tong_thang = tong_ngay // 30
                if tong_thang <= 0:
                    rec.thoigian_hoc = f"{tong_ngay} ngày"
                else:
                    nam = tong_thang // 12
                    thang = tong_thang % 12

                    parts = []
                    if nam > 0:
                        parts.append(f"{nam} năm")
                    if thang > 0:
                        parts.append(f"{thang} tháng")

                    rec.thoigian_hoc = " ".join(parts) if parts else f"{tong_ngay} ngày"



        





