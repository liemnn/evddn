import logging
from odoo import models, fields, api, exceptions
from datetime import date
import calendar

import logging
_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import giaovien_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")




class HocSinhCaCanThiep(models.Model):
    _name = "ekids.hocsinh_ca_canthiep"
    _description = "Cấu hình thiết các ca can thiệp cho học sinh"
    _order = "sequence asc,tu_ngay desc"




    sequence = fields.Integer(string="Thứ tự", default=1)
    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh", required=True, ondelete="cascade")
    name =fields.Char(string="Thời gian áp dụng",compute="_compute_diemdanh_thoigian_hoc_name", readonly=True)

    t2= fields.Boolean(string="T2")
    t3 = fields.Boolean(string="T3")
    t4 = fields.Boolean(string="T4")
    t5 = fields.Boolean(string="T5")
    t6 = fields.Boolean(string="T6")
    t7 = fields.Boolean(string="T7")
    t8 = fields.Boolean(string="CN")

    tu = fields.Char(string="Từ (HH:MM)", help='Format: HH:MM')
    den = fields.Char(string="Đến (HH:MM)", help='Format: HH:MM')

    dm_ca_id = fields.Many2one('ekids.hocphi_dm_ca', string="Loại hình(ca) can thiệp",required=True,ondelete="cascade")
    is_ganthucong =fields.Boolean(string="Người dùng gán thủ công",default=True)
    giaovien_id = fields.Many2one("ekids.giaovien" , string="Giáo viên",ondelete="restrict")
    tien = fields.Float(string='Số tiền(vnđ)', digits=(10, 0),required=True)
    is_hoantien_khi_nghi = fields.Boolean(string="Sẽ [Hoàn tiền] theo quy định khi [Nghỉ]", default=True)

    desc = fields.Html(string="Ghi chú")

    tu_ngay = fields.Date(string="Từ ngày", required=False)
    den_ngay = fields.Date(string="Đến ngày", required=False)
    trangthai = fields.Selection([("0", "Hết hiệu lực")
                                     , ("1", "Còn hiệu lực")]
                                 , compute="_compute_trangthai")

    # (Bổ sung vào phần tính toán trạng thái hiệu lực)
    @api.depends('tu_ngay', 'den_ngay')
    def _compute_trangthai(self):
        today = date.today()
        thang = today.month
        nam = today.year
        days = ngay_util.func_get_cacngay_trong_thang(nam,thang)
        ngay_dauthang = days[0]
        ngay_cuoithang = days[len(days)-1]

        for record in self:
            trangthai = record.func_tinhtoan_trangthai_theo_ngay(ngay_dauthang,ngay_cuoithang)
            record.trangthai = trangthai

    def func_tinhtoan_trangthai_theo_ngay(self, tu_ngay, den_ngay):
        trangthai = "1"

        # Ép kiểu an toàn về Date để tránh lỗi so sánh datetime vs date
        d_tu_ngay = fields.Date.to_date(self.tu_ngay) if self.tu_ngay else None
        d_den_ngay = fields.Date.to_date(self.den_ngay) if self.den_ngay else None
        arg_tu = fields.Date.to_date(tu_ngay) if tu_ngay else None
        arg_den = fields.Date.to_date(den_ngay) if den_ngay else None

        # Nếu self.tu_ngay có giá trị VÀ lớn hơn ngày kết thúc khoảng xét (den_ngay) -> Hết hiệu lực ("0")
        if d_tu_ngay and arg_den and d_tu_ngay > arg_den:
            trangthai = "0"

        # Nếu self.den_ngay có giá trị VÀ nhỏ hơn ngày bắt đầu khoảng xét (tu_ngay) -> Hết hiệu lực ("0")
        elif d_den_ngay and arg_tu and d_den_ngay < arg_tu:
            trangthai = "0"

        return trangthai


    @api.onchange('dm_ca_id')
    def _onchange_hocsinh_ca_canthiep_dm_ca_id(self):
        for record in self:
            if record.dm_ca_id:
                record.tien = record.dm_ca_id.tien
                record.desc = record.dm_ca_id.desc
                record.is_hoantien_khi_nghi =record.dm_ca_id.is_hoantien_khi_nghi
            else:
                record.tien = 0
                record.desc = ""
                record.is_hoantien_khi_nghi =True


    def _compute_diemdanh_thoigian_hoc_name(self):
        for e in self:
            day =""
            if e.t2:
                day+= "T2 "
            if e.t3:
                day+= "T3 "
            if e.t4:
                day+= "T4 "
            if e.t5:
                day+= "T5 "
            if e.t6:
                day+= "T6 "
            if e.t7:
                day+= "T7 "
            if e.t8:
                day+= "CN "
            e.name=day

    def func_kiemtra_ca_hocnay_co_chophep(self,ngay:date.today()):
        weekday = ngay.weekday() +2
        thu_field = 't' + str(weekday )
        is_hoc = getattr(self, thu_field)
        return is_hoc

    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            coso = None
            coso_id = self.env.context.get('default_coso_id') or vals.get('coso_id')
            if not coso_id:
                if vals['hocsinh_id']:
                    hs = self.env['ekids.hocsinh'].browse(vals['hocsinh_id'])
                    if hs:
                        coso_id = hs.coso_id.id
            vals['coso_id'] = coso_id
            result =super(HocSinhCaCanThiep, self).create(vals)
            if result:
                records.append(result)
        return records[0] if len(records) == 1 else records


