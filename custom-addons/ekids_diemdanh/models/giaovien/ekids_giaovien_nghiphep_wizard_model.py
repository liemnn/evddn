from odoo import models, fields, api, _

from odoo.exceptions import UserError
from datetime import datetime, timedelta,date
from odoo.exceptions import ValidationError
import calendar


class ChamCongGiaoVienNghiPhepWizard(models.TransientModel):
    _name = 'ekids.chamcong_giaovien_nghiphep_wizard'
    _description = 'Chọn ngày điểm danh'

    coso_id = fields.Many2one("ekids.coso", related="giaovien_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    giaovien_id = fields.Many2one("ekids.giaovien", string="Giáo viên", required=True, ondelete="cascade")
    tu_ngay = fields.Date(string="Nghỉ từ ngày", required=True)
    den_ngay = fields.Date(string="Nghỉ đến ngày", required=True)
    desc = fields.Html(string="Lý do nghỉ")
    loai = fields.Selection([("0", "Nghỉ tính vào phép (không trừ lương)")
                                , ("1", "Nghỉ (bị trừ lương)")
                                , ("2", "Nghỉ hưởng BHXH (Ốm,đẻ...)")

                             ], default="1")

    @api.constrains('tu_ngay', 'den_ngay')
    def _constrains_nghiLe(self):
        for rec in self:
            if rec.tu_ngay > rec.den_ngay:
                raise ValidationError("Chọn [Ngày bắt đầu] phải nhỏ hơn [Ngày kết thúc]")


    def action_tao_chamcong_giaovien_nghiphep(self):
        context =self.env.context
        for record in self:
            data ={
                'giaovien_id':record.giaovien_id.id,
                'tu_ngay': record.tu_ngay,
                'den_ngay': record.den_ngay,
                'desc': record.desc,
                'loai': record.loai,


            }
            nghiphep = self.env['ekids.giaovien_nghiphep'].create(data)
            if nghiphep:
                record.func_capnhat_chamcong_giaovien2ngay()

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
                setattr(giaovien2thang, field_d, '4')
                ngay += timedelta(days=1)







