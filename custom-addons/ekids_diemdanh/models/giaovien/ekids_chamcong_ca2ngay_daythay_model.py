from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError
import calendar
from .ekids_chamcong_func_abstractmodel import  ChamCongFuncAbstractModel


import logging
_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import giaovien_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")



class ChamCongCa2NgayDayThay(models.Model,ChamCongFuncAbstractModel):
    _name = "ekids.chamcong_ca2ngay_daythay"
    _description = "Điểm danh học sinh theo học"
    _order = "giaovien_id asc"

    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True,
                              ondelete="restrict")

    congviec2thang_id = fields.Many2one("ekids.chamcong_congviec2thang", string="Thuộc",required=True, ondelete="cascade")
    giaovien_id = fields.Many2one('ekids.giaovien', string="Giáo viên dạy thay", stored=True,
                                required=True,ondelete="cascade")

    giaovien_nghi_id = fields.Many2one('ekids.giaovien', string="Dạy thay cho Giáo viên",
                                  domain="[('coso_id','=',coso_id)]", required=True, ondelete="cascade")

    ngay = fields.Date(string="Ngày điểm danh", required=True)

    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh",  domain="[('coso_id','=',coso_id)]",required=True, ondelete="cascade")

    desc = fields.Char(string="Mô tả")

    def _compute_giaovien_id(self):
        for record in self:
            record.giaovien_id = record.congviec2thang_id.giaovien_id.id





