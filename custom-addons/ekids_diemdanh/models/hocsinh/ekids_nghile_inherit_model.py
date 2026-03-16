from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class NghiLeInherit(models.Model):
    _inherit = "ekids.nghile"


    ca2ngay_ids = fields.One2many("ekids.diemdanh_ca2ngay",
                                        compute="_compute_ca2ngay_ids",
                                        string="Điểm danh theo ngày học sinh")


    def _compute_ca2ngay_ids(self):
        context =self.env.context
        hocsinh_id =context.get("default_hocsinh_id")
        ngaystr =context.get("default_ngay")
        date_obj = datetime.strptime(ngaystr, "%Y-%m-%d").date()
        if hocsinh_id and date_obj:
            for rec in self:
                ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search([
                        ('hocsinh_id', '=', hocsinh_id),
                        ('ngay', '=', date_obj),
                        ('trangthai', 'in', ['0','1','2','3'])
                    ])
                rec.ca2ngay_ids =ca2ngay_ids