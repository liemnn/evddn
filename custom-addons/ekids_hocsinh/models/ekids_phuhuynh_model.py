from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _  # <-- THÊM DÒNG NÀY
from .ekids_read_group_abstractmodel import ReadGroupAbstractModel
from datetime import datetime,date
class PhuHuynh(models.Model,ReadGroupAbstractModel):
    _name = "ekids.hocsinh_phuhuynh"
    _description = "Đối tượng học sinh của cơ sở"
    _order = "name asc"


    sequence = fields.Integer(string="STT", default=1)
    # thong tin phụ huynh
    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh", required=True, ondelete="restrict", index=True)

    name = fields.Char(string="Họ và tên",required=True)
    dienthoai = fields.Char(string="Điện thoại",required=True)
    email = fields.Char(string="Email")
    dm_tinh_id = fields.Many2one("ekids.dm_tinh", string="Tỉnh",required=True)
    dm_xa_id = fields.Many2one("ekids.dm_xa", string="Xã", domain="[('dm_tinh_id','=',ph_dm_tinh_id)]",required=True)
    diachi_chitiet = fields.Char(string="Số nhà/ đường phố, thôn xóm")
    nghenghiep = fields.Selection([("0", "Tự do")
                                         , ("1", "Nông nghiệp")
                                         , ("2", "Công nhân")
                                         , ("3", "Công chức/viên chức")
                                         , ("4", "Người lao động chi thức")
                                         , ("5", "Người lao động chi thức")
                                      ], string="Nghề nghiệp")
    trinhdo = fields.Selection([("0", "Cơ bản")
                                      , ("1", "Cao đẳng/Đại học")
                                      , ("2", "Thạc sỹ")
                                      , ("3", "Tiến sỹ/Trên tiến sỹ")
                                   ], string="Trình độ học vấn")

    loai = fields.Selection([("0", "Bố"),
                                    ("2", "Mẹ"),
                                    ("3", "Ông/Bà"),
                                    ("4", "Anh chị em"),
                                    ("5", "Khác")
                                         ], "Quan hệ với trẻ")
    desc = fields.Html(string="Ghi chú")



        





