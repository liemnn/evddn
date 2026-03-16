from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta

class NghiLe(models.Model):
    _name = "ekids.nghile"
    _description = "Mô tả về danh mục tỉnh "
    _order = "tu_ngay asc"


    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", related="nam_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    nam_id = fields.Many2one("ekids.nghile_nam", string="Thuộc Năm",required=True,ondelete="cascade")
    name = fields.Char(string="Tên")
    tu_ngay =fields.Date(string="Từ ngày",required=True)
    den_ngay = fields.Date(string="Đến ngày",required=True)
    songay =fields.Integer(string="Số ngày",compute="_compute_nghile_songay")


    loai = fields.Selection([("0", "Nghỉ lễ theo quy định nhà nước")
                                     , ("1", "Nhà trường cho nghỉ(Hoàn một phần tiền học phí, giáo viên hưởng nguyên lương)")
                                     , ("2", "Nhà trường cho nghỉ(Hoàn 100% học phí, giáo viên bị trừ lương)")  ],
                                 string="Loại nghỉ",default='0',required=True)
    trangthai = fields.Selection([("0", "Không áp dụng")
                                , ("1", "Đưa vào áp dụng")
                                ],
                            string="Trạng thái",default='1',required=True)
    desc = fields.Html(string="Mô tả")

    @api.constrains('tu_ngay', 'den_ngay')
    def _constrains_nghiLe(self):
        for rec in self:
            year = int(rec.nam_id.name)
            if rec.tu_ngay and rec.tu_ngay.year != year:
                raise ValidationError("Chọn [Ngày bắt đầu] phải nằm trong năm thiết lập")
            if rec.den_ngay and rec.den_ngay.year != year:
                raise ValidationError("Chọn [Ngày kết thúc] phải nằm trong năm thiết lập")
            if rec.tu_ngay > rec.den_ngay:
                raise ValidationError("Chọn [Ngày kết thúc] phải lớn hơn [Ngày bắt đầu]")

    @api.depends('tu_ngay', 'den_ngay')
    def _compute_nghile_songay(self):
        for record in self:
            if record.tu_ngay and record.den_ngay:
                delta = (record.den_ngay - record.tu_ngay).days
                record.songay = delta + 1 if delta >= 1 else 1
            else:
                record.songay = 1

