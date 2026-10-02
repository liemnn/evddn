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
    giatri =fields.Char(string="Giá trị",digits=(6, 3),default="1.0")

    @api.onchange('giatri')
    def _onchange_giatri_lamtron(self):
        for rec in self:
            lamtron=1
            congviec2thang_giatri = rec.congviec2thang_giatri_id
            if (congviec2thang_giatri
                and congviec2thang_giatri.chamcong_loai2thang_id
                and congviec2thang_giatri.chamcong_loai2thang_id.chamcong_loai_id
                and congviec2thang_giatri.chamcong_loai2thang_id.chamcong_loai_id.dm_chamcong_id):

                dm_chamcong = congviec2thang_giatri.chamcong_loai2thang_id.chamcong_loai_id.dm_chamcong_id
                lamtron =  int(dm_chamcong.lamtron)

            if rec.giatri:
                giatri = float(rec.giatri)
                rec.giatri = str(round(giatri,lamtron))

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
            'tong_str': congviec2thang.tong_str
        }
        return {
            "type": "ir.actions.client",
            "tag": "reload_congviec_jsless",  # tag tùy chọn, bạn định nghĩa trong JS
            "params": result,
        }

