from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DanhMucChinhSachGiamHocPhi(models.Model):
    _name = "ekids.hocphi_dm_chinhsach_giam"
    _description = "Chính sách giảm học phí"
    _order = "sequence desc"

    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")
    name = fields.Char(string="Tên chính sách giảm ",required=True)

    is_giam_theo_tyle = fields.Boolean(string="Giảm theo tỷ lệ % khi bật, theo số tiền khi tăt", default=True)
    tyle_giam = fields.Integer(string="Tỷ lệ % giảm học phí", default=0)

    tien = fields.Float(string='Số tiền(vnđ)', digits=(10, 0))

    desc = fields.Html(string="Mô tả")
    trangthai = fields.Selection([("0", "Không hoạt động")
                                     , ("1", "Đang hoạt động")], default="1", required=True)

    hocsinh_ids = fields.Many2many(comodel_name="ekids.hocsinh"
                                   , relation="ekids_hocphi_dm_chinhsach_giam4hocsinh_rel"
                                   , column1="hocphi_dm_chinhsach_giam_id"
                                   , column2="hocsinh_id"
                                   , string="Các Học sinh")

    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            result = super(DanhMucChinhSachGiamHocPhi, self).create(vals)
            if result:
                result.func_gan_dm_chinhsach_giam_hocphi_cho_hocsinhs(True)
            records.append(result)
        return records[0] if len(records) == 1 else records

    def write(self, vals):
        res = super(DanhMucChinhSachGiamHocPhi, self).write(vals)

        for rec in self:
            rec.func_gan_dm_chinhsach_giam_hocphi_cho_hocsinhs(True)
        return res

    def unlink(self):
        for rec in self:
            if rec.hocsinh_ids:
                rec.func_gan_dm_chinhsach_giam_hocphi_cho_hocsinhs(False)
        return super().unlink()

    def func_gan_dm_chinhsach_giam_hocphi_cho_hocsinhs(self, is_create):
        hocsinhs = self.env['ekids.hocsinh'].search([
            ('coso_id', '=', self.coso_id.id),
            ('trangthai', '=', '1')
        ])
        if hocsinhs:
            for hocsinh in hocsinhs:

                if hocsinh.dm_chinhsach_giam_id.id == self.id:
                    hocsinh.dm_chinhsach_giam_id =None
                # B2: Thêm mới  cho các giáo viên này
            if (is_create and self.hocsinh_ids):
                for hs in self.hocsinh_ids:
                    hs.dm_chinhsach_giam_id =self


