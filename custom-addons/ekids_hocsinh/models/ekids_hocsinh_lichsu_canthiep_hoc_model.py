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
    name = fields.Char(string="Nơi học tập/can thiệp", required=True)
    desc = fields.Char(string="Ghi chú")
    trangthai = fields.Selection([
        ("1", "Đang theo học"),
        ("-1", "Đã nghỉ"),

    ]
        , string="Trạng thái", default="-1", required=True)



        





