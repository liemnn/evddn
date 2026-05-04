from odoo import api, fields, models
from datetime import datetime
import calendar

import logging
_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import formula_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")

class LuongDMChiTra(models.Model):
    _name = "ekids.luong_dm_chitra"
    _description = "Danh mục chi tiêu của cơ sở"
    _order = "sequence asc,name asc"


    sequence = fields.Integer(string="Thứ tự tính toán",required=True,default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")
    dm_chamcong_id = fields.Many2one("ekids.luong_dm_chamcong",
                                     string="Lựa chọn Danh mục [Chấm công/Xác nhận nhiệm vụ (KPI)]", )

    code = fields.Char(string="Mã", required=True)
    name =fields.Char(string="Tên",required=True)
    luong_cocau = fields.Selection(
        [("1", "Được cộng tiền"),
         ("-1", "Bị trừ tiền (giáo viên phải nộp)"),
         ("-2", "Bị trừ tiền (nhà trường thu hộ)"),
         ("0", "Nhà trường chi trả"),
         ("2", "Thông tin"),
         ],string= "Khoản",required=True)

    luong_loai= fields.Selection(
        [("0", "Cố định"),
         ("1", "Có điều kiện")],string= "Là phần lương",required=True)


    dieukien_loai = fields.Selection(
        [("0", "Chấm công - Đi làm"),
         ("2", "Chấm công - Công việc khác(theo ngày)"),
         ("3", "Chấm công - Công việc khác(theo giá trị/ngày)"),
         ("1", "Giao  nhiệm vụ(KPI)")],string= "Lựa chọn loại [Điều kiện] áp dụng")
    is_show_dieukien_loai = fields.Boolean(compute="_compute_is_show_dieukien_loai")

    formula =fields.Text(string="Giá trị/Công thức")

    desc =fields.Text(string="Mô tả/làm rõ")

    parameters = fields.Text(compute="_compute_parameters")

    is_apdung_rieng = fields.Boolean(string="Xem danh sách giáo viên đang áp dụng", default=False)

    giaovien_ids = fields.Many2many(comodel_name="ekids.giaovien"
                                    , relation="ekids_giaovien2luong_dm_chitra_rel"
                                    , column1="dm_chitra_id"
                                    , column2="giaovien_id"
                                    , string="Các giáo viên")



    @api.onchange("dm_chamcong_id")
    def _compute_parameters(self):
        for record in self:
            param=""
            if record.dm_chamcong_id:
                kpis= record.dm_chamcong_id.kpi_ids
                if kpis:
                    for kpi in kpis:
                        param=param+"-$"+kpi.code +":"+kpi.name +"\n"
                    record.parameters= param
                else:
                    record.parameters=""
            else:
                record.parameters = ""



    @api.depends("luong_loai")
    def _compute_is_show_dieukien_loai(self):
        for record in self:
            if record.luong_loai == '1':
                # Chỉ hiển thị khi loại là  Lương có điều kiện
                record.is_show_dieukien_loai = True
            else:
                record.is_show_dieukien_loai = False







    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=50, order=None):
        # Lấy thông tin người dùng hiện tại
        user = self.env.user
        context = self.env.context
        if context.get('default_coso_id'):
            domain += [('coso_id', '=', context.get('default_coso_id'))]  # Thêm điều kiện cho
        if context.get('type'):
            domain += [('luong_cocau', '=', context.get('type'))]  # Thêm điều kiện cho
        return super().search_fetch(domain, field_names, offset, limit, order)

    def action_gan_cautruc_luong_cho_giaoviens(self):
       giaoviens = None
       for dm in self:
           if not giaoviens:
               giaoviens = self.env['ekids.giaovien'].search([
                   ('coso_id', '=', dm.coso_id.id),
                   ('trangthai', '=', '1')
               ])
           if giaoviens:
               for giaovien in giaoviens:
                    cautruc_luong_ids =giaovien.cautruc_luong_ids
                    #B1: Xóa cấu trúc lương đã gán cho giáo viên này
                    if cautruc_luong_ids:
                        for cautruc_luong_id in cautruc_luong_ids:
                            if cautruc_luong_id.id == dm.id:
                                cautruc_luong_id.unlink()



    def action_xoa_cautruc_luong_cho_giaoviens(self):
        giaoviens =None
        for dm in self:
            if not giaoviens:
                giaoviens = self.env['ekids.giaovien'].search([
                    ('coso_id', '=', dm.coso_id.id),
                    ('trangthai', '=', '1')
                ])
            if giaoviens:
                for giaovien in giaoviens:
                    cautruc_luong_ids = giaovien.cautruc_luong_ids
                    # B1: Xóa cấu trúc lương đã gán cho giáo viên này
                    if cautruc_luong_ids:
                        for cautruc_luong_id in cautruc_luong_ids:
                            if cautruc_luong_id.id == dm.id:
                                cautruc_luong_id.unlink()
