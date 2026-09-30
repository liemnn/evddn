import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HocPHiDanhMuc(models.Model):
    _name = "ekids.luong_dm"
    _description = "Cấu hình học phí để in "
    _order = 'sequence asc'

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")
    sequence = fields.Integer(string="STT", default=1)
    name = fields.Char(string="Tên", required=True)
    trangthai = fields.Selection([("0", "Không hoạt động")
            , ("1", "Đang hoạt động")]
                                 , default="1", string="Trạng thái")

    dm_chitra_ids = fields.One2many("ekids.luong_dm_chitra",
                                        "dm_luong_id", string="Ca/Dịch vụ")
