import logging
from odoo import models, fields, api, exceptions
from datetime import date,datetime,timedelta


_logger = logging.getLogger(__name__)
class GiaoVienNghiPhepInherit(models.Model):
    _inherit = "ekids.giaovien_nghiphep"



    ca2ngay_ids = fields.One2many("ekids.diemdanh_ca2ngay",
                                  compute="_compute_ca2ngay_ids",
                                  string="Điểm danh theo ngày học sinh")

    def _compute_ca2ngay_ids(self):
        context = self.env.context
        giaovien_id = context.get("default_giaovien_id")
        ngaystr = context.get("default_ngay")
        for rec in self:
            if giaovien_id and ngaystr:
                date_obj = datetime.strptime(ngaystr, "%Y-%m-%d").date()
                ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search([
                    ('giaovien_id', '=', giaovien_id),
                    ('ngay', '=', date_obj),
                    ('trangthai', 'in', ['0', '1', '2', '3'])
                ])
                rec.ca2ngay_ids = ca2ngay_ids
            else:
                rec.ca2ngay_ids =None

    def action_xoa_giaovien_nghiphep(self):
        for record in self:
            record.func_capnhat_chamcong_giaovien2ngay()
            record.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def func_capnhat_chamcong_giaovien2ngay(self):
        tu_ngay = self.tu_ngay
        den_ngay = self.den_ngay
        thang = tu_ngay.month
        nam = tu_ngay.year

        giaovien2thang = self.env['ekids.chamcong_giaovien2thang'].search([
            ('giaovien_id', '=',self.giaovien_id.id),
            ('chamcong_loai2thang_id.thang', '=', str(thang)),
            ('chamcong_loai2thang_id.nam', '=', str(nam)),
        ], limit=1)

        if giaovien2thang:
            ngay = tu_ngay
            field_d = "d" + str(tu_ngay.day)
            while ngay <= den_ngay:
                field_d = "d" + str(ngay.day)
                setattr(giaovien2thang, field_d, '1')
                ngay += timedelta(days=1)
