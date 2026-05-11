from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError
import calendar

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


class ChamCongCongViec2NgayGiaTriWizard(models.TransientModel):
    _name = "ekids.chamcong_congviec2ngay_giatri_wizard"
    _description = "Điểm danh học sinh theo ngày"

    congviec2thang_giatri_id = fields.Many2one("ekids.chamcong_congviec2thang_giatri", required=True,ondelete="cascade")
    ngay =fields.Date(string="Ngày")
    giatri =fields.Float(string="Giá trị",digits=(6, 1),default=1)

    is_dl_clocked = fields.Boolean("Khóa dữ liệu không cho sửa", readonly=True, compute="_compute_is_dl_clocked")


    def _compute_is_dl_clocked(self):
        today = date.today()
        sothang_today = (today.year * 12) + today.month

        for record in self:
            coso = record.congviec2thang_giatri_id.coso_id
            nam = record.ngay.year
            thang =  record.ngay.year

            sothang_khoa = int(coso.sothang_khoa_dl_chitieu)
            sothang_dl = (int(record.nam_id.name) * 12) + int(record.name)
            if (sothang_today - sothang_dl) >= sothang_khoa:
                record.is_dl_clocked = True
            else:
                record.is_dl_clocked = False

    def action_capnhat_ketqua_congviec2ngay_giatri(self):
        context = self.env.context
        congviec2thang = self.congviec2thang_giatri_id
        ngay =self.ngay
        day =ngay.day
        field_day = "d"+str(day)
        setattr(congviec2thang,field_day,self.giatri)


        result = {
            "record_id": congviec2thang.id,
            "ngay_field": field_day,
            "giatri": self.giatri,
            'tong': congviec2thang.tong
        }
        return {
            "type": "ir.actions.client",
            "tag": "reload_congviec_jsless",  # tag tùy chọn, bạn định nghĩa trong JS
            "params": result,
        }

    def write(self, vals):
        nam = int(self.ngay.year)
        thang = int(self.ngay.month)
        coso = self.congviec2thang_giatri_id.coso_id

        coso_util.func_is_dl_diemdanh_locked(coso
                                              , nam
                                              , thang)

        return super(ChamCongCongViec2NgayGiaTriWizard, self).write(vals)

