from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError
import calendar


class DiemDanhHocSinh2Ngay(models.Model):
    _name = "ekids.diemdanh_hocsinh2ngay"
    _description = "Điểm danh học sinh theo ngày"

    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh", required=True, ondelete="restrict", index=True)
    ngay =fields.Date(string="Ngày")
    trangthai = fields.Selection([
        ('1', "Đi học"),
        ("0", "Đi học nửa buổi"),
        ("-1", "Nghỉ học")

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
                    ('hocsinh_id', '=', self.hocsinh_id.id),
                    ('ngay', '=', self.ngay),
                    ('trangthai', 'in', ['-1','0','1','2','3'])
                ])
            rec.ca2ngay_ids =ca2ngay_ids
    def _compute_ca2ngay_hocbu_ids(self):
        for rec in self:
            ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search([
                    ('hocsinh_id', '=', self.hocsinh_id.id),
                    ('ngay', '=', self.ngay),
                    ('trangthai', 'in', ['4','5'])
                ])
            rec.ca2ngay_hocbu_ids =ca2ngay_ids

    def action_xac_nhan(self):
        # đóng popup và refresh view cha
        record_id =self.env.context.get("default_record_id")
        day = self.ngay.day
        thang =self.ngay.month
        nam =self.ngay.year
        hocsinh2thang = self.env['ekids.diemdanh_hocsinh2thang'].search([
            ('hocsinh_id', '=', self.hocsinh_id.id),
            ('diemdanh_id.nam', '=', str(nam)),
            ('diemdanh_id.thang', '=', str(thang)),

        ], limit=1)

        if hocsinh2thang:
           ngay_field = 'd' + str(day)
           setattr(hocsinh2thang,ngay_field,self.trangthai)
           #cap nhat ca2ngay cho hocsinh để hoàn trả hoc phí
           self.func_capnhat_diemdanh_ca2ngay_khi_diemdanh(self.hocsinh_id.id,self.ngay,self.trangthai)
           # Trả về action client đặc biệt
           trangthai =self.trangthai
           if trangthai =='1' or trangthai =='11':
               count = self.func_is_co_ca_hocbu_tangcuong(self.hocsinh_id.id,self.ngay)
               if count > 0:
                   trangthai='11'
                   setattr(hocsinh2thang,ngay_field,trangthai)
               else:
                   trangthai='1'
           result={
               "record_id": record_id,
               "ngay_field":ngay_field,
               "giatri":trangthai
           }
           return {
               "type": "ir.actions.client",
               "tag": "reload_jsless",  # tag tùy chọn, bạn định nghĩa trong JS
               "params": result,
           }

    def func_is_co_ca_hocbu_tangcuong(self, hocsinh_id, ngay):
       count = self.env['ekids.diemdanh_ca2ngay'].search_count([
           ('hocsinh_id', '=', hocsinh_id),
           ('ngay', '=', ngay),
           ('trangthai', 'in', ['4', '5'])
       ])
       return count

           #return {"type": "ir.actions.client", "tag": "reload"}
    def func_capnhat_diemdanh_ca2ngay_khi_diemdanh(self,hocsinh_id,ngay,trangthai):
        if trangthai == '-1':
            ca2ngays = self.env['ekids.diemdanh_ca2ngay'].search([
                ('hocsinh_id', '=', hocsinh_id),
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
                    'default_hocsinh_id': self.hocsinh_id.id,
                    'default_ngay': self.ngay,
                    'default_is_diemdanh_hocsinh':True
                 }
        }


    def action_quanly_nghiphep_hocsinh(self):
        ctx = dict(self.env.context)
        hocsinh_id = ctx.get('default_hocsinh_id')
        ngay = ctx.get('default_ngay')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nghỉ phép',
            'res_model': 'ekids.diemdanh_hocsinh_nghiphep_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context':
                {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': hocsinh_id,
                    'default_tu_ngay': ngay,
                    'default_den_ngay': ngay,
                }
        }



