from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError
import calendar


class ChamCongGiaoVien2Ngay(models.Model):
    _name = "ekids.chamcong_giaovien2ngay"
    _description = "Điểm danh học sinh theo ngày"

    coso_id = fields.Many2one("ekids.coso", related="giaovien_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    giaovien_id = fields.Many2one("ekids.giaovien", string="Giáo viên", required=True, ondelete="restrict", index=True)
    ngay =fields.Date(string="Ngày")
    trangthai = fields.Selection([
        ('1', "Đi Làm"),
        ('10', "Đi Làm (đi muộn)"),
        ("0", "Đi Làm nửa buổi"),
        ("-1", "Nghỉ làm")

    ], string="Xác nhận", required=True, default="1")



    ca2ngay_ids = fields.One2many("ekids.diemdanh_ca2ngay",
                                    compute="_compute_ca2ngay_ids",
                                    string="Điểm danh theo ngày học sinh")
    ca2ngay_hocbu_ids = fields.One2many("ekids.diemdanh_ca2ngay",
                                  compute="_compute_ca2ngay_hocbu_ids",
                                  string="Điểm danh theo ngày học sinh")


    def _compute_ca2ngay_ids(self):
        for rec in self:
            ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search([
                    ('giaovien_id', '=', self.giaovien_id.id),
                    ('ngay', '=', self.ngay),
                    ('trangthai', 'in', ['0','1','2','3'])
                ])
            rec.ca2ngay_ids =ca2ngay_ids
    def _compute_ca2ngay_hocbu_ids(self):
        for rec in self:
            ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search([
                    ('giaovien_id', '=', self.giaovien_id.id),
                    ('ngay', '=', self.ngay),
                    ('trangthai', '=', '4')
                ])
            rec.ca2ngay_hocbu_ids =ca2ngay_ids

    def action_xac_nhan(self):
        # đóng popup và refresh view cha
        record_id =self.env.context.get("default_record_id")
        day = self.ngay.day
        thang =self.ngay.month
        nam =self.ngay.year
        giaovien2thang = self.env['ekids.chamcong_giaovien2thang'].search([
            ('giaovien_id', '=', self.giaovien_id.id),
            ('chamcong_loai2thang_id.chamcong_loai_id.loai', '=', '0'),
            ('chamcong_loai2thang_id.nam', '=', str(nam)),
            ('chamcong_loai2thang_id.thang', '=', str(thang)),

        ], limit=1)

        if giaovien2thang:
           ngay_field = 'd' + str(day)
           setattr(giaovien2thang,ngay_field,self.trangthai)
           #cap nhat ca2ngay cho hocsinh để hoàn trả hoc phí
           self.func_capnhat_diemdanh_ca2ngay_khi_chamcong(self.giaovien_id.id,self.ngay,self.trangthai)
           # Trả về action client đặc biệt
           giaovien2thang.func_tinhtoan_cac_giatri_tong()
           result={
               "record_id": record_id,
               "ngay_field":ngay_field,
               "giatri":self.trangthai,
               "tong": giaovien2thang.tong_dilam_chamcong
           }
           return {
               "type": "ir.actions.client",
               "tag": "reload_chamcong_jsless",  # tag tùy chọn, bạn định nghĩa trong JS
               "params": result,
           }

           #return {"type": "ir.actions.client", "tag": "reload"}
    def func_capnhat_diemdanh_ca2ngay_khi_chamcong(self,giaovien_id,ngay,trangthai):
        if trangthai =='-1':
            ca2ngays = self.env['ekids.diemdanh_ca2ngay'].search([
                ('giaovien_id', '=', giaovien_id),
                ('ngay', '=', ngay)

            ])
            if ca2ngays:
                for ca2ngay in ca2ngays:
                    if ca2ngay.trangthai =='0':
                        ca2ngay.trangthai =trangthai



    def action_open_popup_tao_hocsinh2ngay_hocbu(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Điểm danh ngày',
            'res_model': 'ekids.diemdanh_ca2ngay_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context':
                {
                    'default_coso_id': self.coso_id.id,
                    'default_giaovien_id': self.giaovien_id.id,
                    'default_ngay': self.ngay,
                    'is_giaovien_tao': True

                 }
        }

    def action_open_popup_tao_hocsinh2ngay_hocbu_tu_giaovien(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Điểm danh ngày',
            'res_model': 'ekids.diemdanh_ca2ngay_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context':
                {
                    'default_coso_id': self.coso_id.id,
                    'default_giaovien_id': self.giaovien_id.id,
                    'default_ngay': self.ngay,
                    'is_giaovien_tao': True

                 }
        }

    def action_quanly_nghiphep_giaovien(self):
        ctx = dict(self.env.context)
        giaovien_id = ctx.get('default_giaovien_id')
        ngay = ctx.get('default_ngay')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nghỉ phép',
            'res_model': 'ekids.chamcong_giaovien_nghiphep_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context':
                {
                    'default_coso_id': self.coso_id.id,
                    'default_giaovien_id': giaovien_id,
                    'default_tu_ngay': ngay,
                    'default_den_ngay': ngay,
                }
        }

