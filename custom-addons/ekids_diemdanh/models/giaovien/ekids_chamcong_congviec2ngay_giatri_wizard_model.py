from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError
import calendar



class ChamCongCongViec2NgayGiaTriWizard(models.TransientModel):
    _name = "ekids.chamcong_congviec2ngay_giatri_wizard"
    _description = "Điểm danh học sinh theo ngày"

    congviec2thang_giatri_id = fields.Many2one("ekids.chamcong_congviec2thang_giatri", required=True,ondelete="cascade")
    ngay =fields.Date(string="Ngày")
    giatri =fields.Float(string="Giá trị",digits=(6, 1),default=1)

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

