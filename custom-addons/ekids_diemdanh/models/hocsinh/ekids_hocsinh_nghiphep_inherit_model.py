import logging
from odoo import models, fields, api, exceptions
from datetime import datetime, timedelta,date


_logger = logging.getLogger(__name__)

import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
    from odoo.addons.ekids_func import hocsinh_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")


class HocSinhNghiPhepInherit(models.Model):
    _inherit = "ekids.hocsinh_nghiphep"



    ca2ngay_ids = fields.One2many("ekids.diemdanh_ca2ngay",
                                  compute="_compute_ca2ngay_ids",
                                  string="Điểm danh theo ngày học sinh")

    def _compute_ca2ngay_ids(self):
        context = self.env.context
        hocsinh_id = context.get("default_hocsinh_id")
        ngaystr = context.get("default_ngay")
        date_obj = datetime.strptime(ngaystr, "%Y-%m-%d").date()
        if hocsinh_id and date_obj:
            for rec in self:
                ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search([
                    ('hocsinh_id', '=', hocsinh_id),
                    ('ngay', '=', date_obj),
                    ('trangthai', 'in', ['0', '1', '2', '3'])
                ])
                rec.ca2ngay_ids = ca2ngay_ids

    def action_xoa_hocsinh_nghiphep(self):
        for record in self:
            record.func_update_diemdanh_hocsinh2ngay()
            record.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def func_update_diemdanh_hocsinh2ngay(self):
        tu_ngay = self.tu_ngay
        den_ngay = self.den_ngay
        thang = tu_ngay.month
        nam = tu_ngay.year
        hocsinh2thang = self.env['ekids.diemdanh_hocsinh2thang'].search([
            ('hocsinh_id', '=', self.hocsinh_id.id),
            ('diemdanh_id.thang', '=', str(thang)),
            ('diemdanh_id.nam', '=', str(nam)),
        ],limit=1)
        if hocsinh2thang:
            ngay = tu_ngay
            field_d="d"+ str(tu_ngay.day)
            while ngay <= den_ngay:
                if self.is_se_hocbu:
                    hocsinh_util.func_capnhat_macdinh_diemdanh_ca2ngay_theo_ngay_nghiphep(self, hocsinh2thang.hocsinh_id, ngay)
                field_d = "d"+ str(ngay.day)
                setattr(hocsinh2thang, field_d, '1')
                ngay += timedelta(days=1)
