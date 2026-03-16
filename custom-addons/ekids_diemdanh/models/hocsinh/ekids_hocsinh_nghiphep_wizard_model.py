from odoo import models, fields, api, _

from odoo.exceptions import UserError
from datetime import datetime, timedelta,date
from odoo.exceptions import ValidationError
import calendar


class DiemDanhHocSinhNghiPhepWizard(models.TransientModel):
    _name = 'ekids.diemdanh_hocsinh_nghiphep_wizard'
    _description = 'Chọn ngày điểm danh'

    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh", required=True, ondelete="cascade")
    tu_ngay = fields.Date(string="Nghỉ từ ngày", required=True)
    den_ngay = fields.Date(string="Nghỉ đến ngày", required=True)
    desc = fields.Html(string="Lý do nghỉ")
    is_hoantra_hocphi = fields.Boolean(string="Cho phép thiết lập % hoàn trả [Học phí] riêng", default=False)
    tyle_hoantra_hocphi = fields.Integer(string="Tỷ lệ % sẽ được hoàn trả [Học phí] tháng tơi", default=0)

    @api.constrains('tu_ngay', 'den_ngay')
    def _constrains_nghiLe(self):
        for rec in self:
            if rec.tu_ngay > rec.den_ngay:
                raise ValidationError("Chọn [Ngày bắt đầu] phải nhỏ hơn [Ngày kết thúc]")


    def action_tao_diemdanh_hocsinh_nghiphep(self):
        context =self.env.context
        for record in self:
            data ={
                'hocsinh_id':record.hocsinh_id.id,
                'tu_ngay': record.tu_ngay,
                'den_ngay': record.den_ngay,
                'desc': record.desc,
                'is_hoantra_hocphi': record.is_hoantra_hocphi,
                'tyle_hoantra_hocphi': record.tyle_hoantra_hocphi,

            }
            nghiphep = self.env['ekids.hocsinh_nghiphep'].create(data)
            if nghiphep:
                record.func_update_diemdanh_hocsinh2ngay()

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
                field_d = "d"+ str(ngay.day)
                setattr(hocsinh2thang, field_d, '4')
                ngay += timedelta(days=1)





