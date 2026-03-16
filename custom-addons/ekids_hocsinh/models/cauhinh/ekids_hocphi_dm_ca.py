from odoo import api, fields, models
from datetime import datetime
import calendar
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class DanhMucCa(models.Model):
    _name = 'ekids.hocphi_dm_ca'
    _description = 'Danh mục ca theo từng cơ sở'
    _order = "sequence asc"


    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")
    name = fields.Char(string="Tên loại hình [Ca] can thiệp",required=True)
    tien = fields.Float(string='Số tiền(vnđ)', digits=(10, 0),required=True)
    is_hoantien_khi_nghi = fields.Boolean(string="Sẽ [Hoàn tiền] theo quy định khi [Nghỉ]", default=True)
    is_giam_hocphi = fields.Boolean(string="Được tính toán giảm [học phí] (nếu có)", default=True)

    desc = fields.Char(string="Mô tả")
    is_apdung_rieng =fields.Boolean(string="Thiết lập [Riêng] cho một số học sinh",default=False)

    t2 = fields.Boolean(string="T2")
    t3 = fields.Boolean(string="T3")
    t4 = fields.Boolean(string="T4")
    t5 = fields.Boolean(string="T5")
    t6 = fields.Boolean(string="T6")
    t7 = fields.Boolean(string="T7")
    t8 = fields.Boolean(string="CN")

    tu = fields.Char(string="Từ (HH:MM)", help='Format: HH:MM')
    den = fields.Char(string="Đến (HH:MM)", help='Format: HH:MM')

    trangthai = fields.Selection([("0", "Không hoạt động")
                                     , ("1", "Đang hoạt động")],default="1",string="Trạng thái")
    giaovien_id = fields.Many2one("ekids.giaovien"
                                  , string="Giáo viên", ondelete="restrict")

    hocsinh_ids = fields.Many2many(comodel_name="ekids.hocsinh"
                                   , relation="ekids_hocphi_dm_ca4hocsinh_rel"
                                   , column1="hocphi_dm_ca_id"
                                   , column2="hocsinh_id"
                                   , string="Các Học sinh")

    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            result = super(DanhMucCa, self).create(vals)
            if result:
                result.func_gan_dm_ca_cho_hocsinhs(True)
            records.append(result)
        return records[0] if len(records) == 1 else records

    def write(self, vals):
        res = super(DanhMucCa, self).write(vals)

        # Logic xử lý khi danh sách học sinh thay đổi
        for rec in self:
            rec.func_gan_dm_ca_cho_hocsinhs(True)
        return res

    def unlink(self):
        for rec in self:
            if rec.hocsinh_ids:
                rec.func_gan_dm_ca_cho_hocsinhs(False)
        return super().unlink()

    def func_gan_dm_ca_cho_hocsinhs(self, is_create):
        hocsinhs = self.env['ekids.hocsinh'].search([
            ('coso_id', '=', self.coso_id.id),
            ('trangthai', '=', '1')
        ])
        if hocsinhs:
            for hocsinh in hocsinhs:
                ca_canthiep_ids = hocsinh.ca_canthiep_ids
                # B1: Xóa cấu trúc lương đã gán cho giáo viên này
                if ca_canthiep_ids:
                    for ca_canthiep_id in ca_canthiep_ids:
                        is_ganthucong =ca_canthiep_id.is_ganthucong
                        if (is_ganthucong == False
                                and ca_canthiep_id.dm_ca_id.id == self.id):
                            ca_canthiep_id.unlink()
                        elif (is_ganthucong == True
                                and ca_canthiep_id.dm_ca_id.id == self.id):
                            # Cập nhật cho gán thu cong
                            if is_create == True:
                                self.func_update_ca_canthiep_cho_hocsinh(ca_canthiep_id, self)

                # B2: Thêm mới  cho các giáo viên này
            if (is_create==True and self.hocsinh_ids):
                for hs in self.hocsinh_ids:
                    self.func_taomoi_ca_canthiep_cho_hocsinh(hs, self)
    def func_update_ca_canthiep_cho_hocsinh(self,ca_canthiep,dm):
        data = {
            "name": dm.name,
            "tien": dm.tien,
            "desc": dm.desc,
        }
        ca_canthiep.write(data)



    def func_taomoi_ca_canthiep_cho_hocsinh(self,hocsinh,dm):
        data = {
            "coso_id": hocsinh.coso_id.id,
            "hocsinh_id": hocsinh.id,
            "name": dm.name,
            "t2":dm.t2,
            "t3": dm.t3,
            "t4": dm.t4,
            "t5": dm.t5,
            "t6": dm.t6,
            "t7": dm.t7,
            "t8": dm.t8,
            "tu":dm.tu,
            "den" :dm.den,
            "dm_ca_id":dm.id,
            "tien": dm.tien,
            "desc": dm.desc,
            'is_ganthucong':False
        }
        if self.giaovien_id:
            data['giaovien_id']= self.giaovien_id.id
        self.env['ekids.hocsinh_ca_canthiep'].create(data)

    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=50, order=None):
        # Lấy thông tin người dùng hiện tại
        user = self.env.user
        context = self.env.context

        if context.get('default_coso_id'):
            domain += [('coso_id', '=', context.get('default_coso_id'))]  # Thêm điều kiện cho
        else:
            domain += [('coso_id', '=', -1)]  # Thêm điều kiện cho
        return super().search_fetch(domain, field_names, offset, limit, order)



