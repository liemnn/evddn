from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError
import calendar


class DiemDanhCa2Ngay(models.Model):
    _name = "ekids.diemdanh_ca2ngay"
    _description = "Điểm danh học sinh theo ngày can thiệp"

    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")


    hocphi_dm_ca_id = fields.Many2one("ekids.hocphi_dm_ca",required=True,
                                      string="Loại hình Ca/dịch vụ", index=True, ondelete="cascade")

    hocsinh_ca_canthiep_id = fields.Many2one("ekids.hocsinh_ca_canthiep",
                                      string="Thuộc cấu hình", index=True, ondelete="cascade")


    ngay = fields.Date(string="Ngày điểm danh",required=True)

    tu = fields.Char(string="Từ (HH:MM)", help='Format: HH:MM')
    den = fields.Char(string="Đến (HH:MM)", help='Format: HH:MM')

    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh", required=True, ondelete="restrict",index=True)
    giaovien_id = fields.Many2one("ekids.giaovien", string="Giáo viên thực hiện", ondelete="restrict",index=True)

    trangthai = fields.Selection([
        ("0", "Đợi xác thực"),
        ("1", "Đã được học"),
        ("-1","Không học"),
        ("2", "Nghỉ - Hoàn trả học phí"),
        ("3", "Nghỉ - Sẽ sắp lịch dạy bù"),
        ("4", "Đã dạy bù"),
        ("5", "Tăng cường"),
    ], string="Xác nhận", required=True, default="1")

    desc = fields.Char(string="Mô tả")

    is_hoc = fields.Boolean(compute="_compute_is_hoc")
    is_nghi = fields.Boolean(compute="_compute_is_nghi")
    is_nghi_khongbu = fields.Boolean(compute="_compute_is_nghi_khongbu")
    is_nghi_hocbu= fields.Boolean(compute="_compute_is_nghi_hocbu")

    _sql_constraints = [
        ('unique_diemdanh_ca2ngay',
         'UNIQUE(hocphi_dm_ca_id,hocsinh_id,giaovien_id,ngay)',
         'Đã tồn tại [Ca can thiệp trong ngày]  của học sinh, vui lòng kiểm tra lại !')
    ]


    @api.onchange('trangthai')
    def _onchage_trangthai(self):
        for rec in self:
            if rec.trangthai == '1':
                rec.is_hoc = True
            else:
                rec.is_hoc = False


    def _compute_is_hoc(self):
        for rec in self:
            if rec.trangthai == '1':
                rec.is_hoc = True
            else:
                rec.is_hoc = False

    def _compute_is_nghi(self):
        for rec in self:
            if rec.trangthai == '-1':
                rec.is_nghi = True
            else:
                rec.is_nghi = False

    def _compute_is_nghi_khongbu(self):
        for rec in self:
            if rec.trangthai == '2':
                rec.is_nghi_khongbu = True
            else:
                rec.is_nghi_khongbu = False
    def _compute_is_nghi_hocbu(self):
        for rec in self:
            if rec.trangthai == '3':
                rec.is_nghi_hocbu= True
            else:
                rec.is_nghi_hocbu = False

    def func_xacnhan_ca2ngay_hoc(self):
        self.trangthai ='1'
        return self.func_diemdanh_hocsinh_get_url_back()


    def func_xacnhan_ca2ngay_nghi_khongbu(self):
        self.trangthai ='2'
        return self.func_diemdanh_hocsinh_get_url_back()

    def func_xacnhan_ca2ngay_nghi_hocbu(self):
        self.trangthai = '3'
        return self.func_diemdanh_hocsinh_get_url_back()


    def func_xacnhan_ca2ngay_hoc_chamcong(self):
        self.trangthai ='1'
        return self.func_chamcong_giaovien_get_url_back()


    def func_xacnhan_ca2ngay_nghi_khongbu_chamcong(self):
        self.trangthai ='2'
        return self.func_chamcong_giaovien_get_url_back()

    def func_xacnhan_ca2ngay_nghi_hocbu_chamcong(self):
        self.trangthai = '3'
        return self.func_chamcong_giaovien_get_url_back()

    def action_xoa_diemdanh_ca2ngay(self):
        nam =self.ngay.year
        thang =self.ngay.month
        ngay =self.ngay.day
        hocsinh_id =self.hocsinh_id.id
        self.unlink()
        return self.func_diemdanh_hocsinh_get_url_back_thang(hocsinh_id,nam, thang, ngay)

    def action_xacnhan_xoa_hocbu_tu_chamcong(self):
        nam = self.ngay.year
        thang = self.ngay.month
        ngay = self.ngay.day
        giaovien_id = self.giaovien_id.id
        self.unlink()
        return self.func_chamcong_giaovien_get_url_back_thang(giaovien_id, nam, thang, ngay)

    def action_xacnhan_xoa_hocbu_tu_giaovien(self):
        nam =self.ngay.year
        thang =self.ngay.month
        ngay =self.ngay.day
        hocsinh_id =self.hocsinh_id.id
        self.unlink()

    def func_diemdanh_hocsinh_get_url_back(self):
        ngay =self.ngay
        hocsinh_id =self.hocsinh_id.id
        giaovien_id = self.giaovien_id.id
        thang = ngay.month
        nam =ngay.year
        day = ngay.day
        return self.func_diemdanh_hocsinh_get_url_back_thang(hocsinh_id,nam,thang,day)

    def func_chamcong_giaovien_get_url_back(self):
        ngay = self.ngay
        hocsinh_id = self.hocsinh_id.id
        giaovien_id = self.giaovien_id.id
        thang = ngay.month
        nam = ngay.year
        day = ngay.day
        return self.func_chamcong_giaovien_get_url_back_thang(giaovien_id, nam, thang, day)



    def func_chamcong_giaovien_get_url_back_thang(self,giaovien_id,nam,thang,ngay):

        giaovien2thang = self.env['ekids.chamcong_giaovien2thang'].search([
            ('giaovien_id', '=', giaovien_id),
            ('chamcong_loai2thang_id.chamcong_loai_id.loai', '=', '0'),
            ('chamcong_loai2thang_id.nam', '=', str(nam)),
            ('chamcong_loai2thang_id.thang', '=', str(thang)),

        ],limit=1)
        if giaovien2thang:
             field_name  =   f'd{ngay}'
             field_value =  getattr(giaovien2thang,field_name)
             return giaovien2thang.action_mo_popup_chamcong_giaovien2thang_ngay(giaovien2thang.id, field_name, field_value)

    def func_diemdanh_hocsinh_get_url_back_thang(self,hocsinh_id,nam,thang,ngay):

        hocsinh2thang = self.env['ekids.diemdanh_hocsinh2thang'].search([
            ('hocsinh_id', '=', hocsinh_id),
            ('diemdanh_id.thang', '=', thang),
            ('diemdanh_id.nam', '=', nam),
        ],limit=1)
        if hocsinh2thang:
             field_name  =   f'd{ngay}'
             field_value =  getattr(hocsinh2thang,field_name)
             return hocsinh2thang.action_mo_popup_diemdanh_theo_ngay(hocsinh2thang.id, field_name, field_value)



    def action_doi_giaovien(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Điểm danh ngày',
            'res_model': 'ekids.diemdanh_ca2ngay',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context':
                {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': self.hocsinh_id.id,
                    'default_ngay': self.ngay,
                    'default_is_diemdanh_hocsinh': True
                }
        }



