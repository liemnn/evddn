from odoo import api, fields, models
from datetime import datetime
import calendar
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
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


class DanhMucCa(models.Model):
    _name = 'ekids.hocphi_dm_ca'
    _description = 'Danh mục ca theo từng cơ sở'
    _order = "sequence asc"


    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")
    name = fields.Char(string="Tên loại hình [Ca] can thiệp",required=True)
    tien = fields.Float(string='Số tiền(vnđ)', digits=(10, 0),required=True)
    is_tien_trongoi = fields.Boolean(string="Số tiền thu được thiết lập trọn gói theo tháng", default=False)

    is_hoantien_khi_nghi = fields.Boolean(string="Sẽ [Hoàn tiền] theo quy định khi [Nghỉ]", default=True)
    tyle_hoan_rieng = fields.Integer(string="% Tỷ lệ [Hoàn tiền] riêng cho khoản này(nếu có)", default=0)
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



    trangthai = fields.Selection([("0", "Không hoạt động")
                                     , ("1", "Đang hoạt động")],default="1",string="Trạng thái")


    is_hoan_hocphi = fields.Boolean(compute="_is_hoan_hocphi")
    tyle_hoan_hocphi = fields.Char(compute="_is_hoan_hocphi")

    dm_hocphi_id = fields.Many2one('ekids.hocphi_dm'
                                   , string='Thuộc mục thu(nếu có)')

    is_xem_hocsinh= fields.Boolean(string="Xem danh sách học sinh đang sử dụng", default=False)

    # Hoặc nếu muốn hiển thị thẳng danh sách học sinh (ekids.hocsinh) thông qua các bản ghi đang cấu hình:
    hocsinh_ca_ids = fields.One2many(
        'ekids.hocsinh_ca_canthiep'
        ,compute="_compute_hocsinh_ca_ids"
        ,string="Cấu hình ca học của học sinh"
    )

    def _compute_hocsinh_ca_ids(self):
        for rec in self:
            # 1. Lọc tất cả các cấu hình ca can thiệp đang hoạt động của ca này
            domain = [
                ('dm_ca_id', '=', rec.id),
                ('hocsinh_id.trangthai', '=', "1")
            ]
            ca_hocsinhs = self.env['ekids.hocsinh_ca_canthiep'].search(domain)

            # 2. Lọc loại bỏ trùng lặp: Mỗi học sinh chỉ lấy duy nhất 1 bản ghi (ví dụ lấy bản ghi đầu tiên hoặc mới nhất)
            hocsinh_da_lay = set()
            ket_qua = self.env['ekids.hocsinh_ca_canthiep']

            for ca in ca_hocsinhs:
                if ca.hocsinh_id.id not in hocsinh_da_lay:
                    hocsinh_da_lay.add(ca.hocsinh_id.id)
                    ket_qua += ca

            # 3. Sắp xếp kết quả trong Python theo đúng thứ tự của học sinh: ngay_nhaphoc asc, create_date asc, id asc
            ket_qua = ket_qua.sorted(key=lambda r: (
                r.hocsinh_id.ngay_nhaphoc or fields.Date.min
            ))

            rec.hocsinh_ca_ids = ket_qua

    def _is_hoan_hocphi(self):

        for record in self:
            is_hoan_hocphi = False
            tyle_hoan_hocphi = "0"
            if record.is_hoantien_khi_nghi == True:
                is_hoan_hocphi = True
                tyle_hoan_hocphi = str(record.coso_id.tyle_tralai_hs_vangmat)
            elif record.tyle_hoan_rieng > 0:
                is_hoan_hocphi = True
                tyle_hoan_hocphi = str(record.tyle_hoan_rieng)
            record.is_hoan_hocphi = is_hoan_hocphi
            record.tyle_hoan_hocphi = tyle_hoan_hocphi





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

    def func_get_dongia_hocsinh(self,hocsinh,tu_ngay,den_ngay):
        #nghiles = nghile_util.func_get_nghiles_trong_khoang_thoigian(self,self.coso_id, ['0'], tu_ngay,den_ngay)
        nghiles =None
        return self.func_get_dongia(nghiles,hocsinh,tu_ngay,den_ngay)


    def func_get_dongia(self,nghiles,hocsinh,tu_ngay,den_ngay):
        if self.is_tien_trongoi == True:
            ngays = hocsinh_util.func_get_ngay_dihoc_kehoachs_dm_ca(nghiles,hocsinh,self,tu_ngay,den_ngay)
            dongia=0
            if len(ngays)>0:
                dongia = self.tien /len(ngays)
            return dongia
        else:
            return  self.tien



    def func_is_hoc(self,hocsinh,ngay):
        week = ngay.weekday() + 2
        field_name_ca = "t" + str(week)
        field_name_hs_cs = "hd_t" + str(week)

        # TH1: có danh mục ca và có áp dụng riêng
        if (self.is_apdung_rieng == True):
            is_hoc = getattr(self, field_name_ca)
            if is_hoc == True:
                return True
        else:
            # TH2: Theo hồ cơ sở
            coso = self.coso_id
            is_hoc = getattr(coso, field_name_hs_cs)
            if is_hoc == True:
                return True

        # còn lại không có
        return False

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



