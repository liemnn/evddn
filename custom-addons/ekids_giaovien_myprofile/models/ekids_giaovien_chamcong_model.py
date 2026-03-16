import typing

from odoo import models, fields, api, _
from odoo.api import ValuesType
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError
import calendar




class GiaoVienChamCong(models.Model):
    _name = "ekids.giaovien_chamcong"
    _description = "Xác nhận cho các ngày"
    _order = "ngay desc"

    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", related="giaovien_id.coso_id", string="Cơ sở", required=True,
                             ondelete="restrict")
    giaovien_id = fields.Many2one('ekids.giaovien', string="Họ và tên",required=True)
    ngay = fields.Date(string="Ngày")
    name = fields.Char("Tháng/Năm", compute="_compute_name",store=True)
    desc = fields.Html(string="Ghi chú")
    xacthuc = fields.Selection([
        ("0", "Đợi xác nhận"),
        ("1", "Đã xác nhận"),
        ("-1", "Quá ngày (không thể xác nhận lại)"),
    ], string="Cần làm", default="0",required=True)

    is_chophep_xacnhan= fields.Boolean(string="Cho phép giáo viên xác nhận cấm công",compute="_compute_is_chophep_xacnhan",default=True)

    trangthai = fields.Selection([
        ('-2', " "),
        ('1', "Đi Làm"),
        ("0", "Đi Làm nửa buổi"),
        ("-1", "Nghỉ làm")

    ], string="Trạng thái", required=True, default="-2")

    ca2ngay_ids = fields.One2many("ekids.diemdanh_ca2ngay",
                                  compute="_compute_ca2ngay_ids",
                                  string="Điểm danh theo ngày học sinh")
    ca2ngay_hocbu_ids = fields.One2many("ekids.diemdanh_ca2ngay",
                                        compute="_compute_ca2ngay_hocbu_ids",
                                        string="Điểm danh theo ngày học sinh")




    _sql_constraints = [
        ('unique_giaovien_chamcong',
         'UNIQUE(giaovien_id,ngay)',
         'Đã tồn tại [Ngày cấm công]  của Giáo viên, vui lòng kiểm tra lại !')
    ]

    def _compute_is_chophep_xacnhan(self):
        for rec in self:
            if rec.ngay:
                thang =rec.ngay.month
                nam =rec.ngay.year
                count= self.env['ekids.luong'].search_count([
                        ('giaovien_id', '=',rec.giaovien_id.id),
                        ('thang_id', '=',str(thang)),
                        ('nam_id', '=', str(nam))])
                if count >0:
                    rec.is_chophep_xacnhan =False

                else:
                    rec.is_chophep_xacnhan= True


    def _compute_ca2ngay_hocbu_ids(self):
        for rec in self:
            ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search([
                ('giaovien_id', '=', self.giaovien_id.id),
                ('ngay', '=', self.ngay),
                ('trangthai', 'in', ['4','5'])
            ])
            rec.ca2ngay_hocbu_ids = ca2ngay_ids


    def _compute_ca2ngay_ids(self):
        for rec in self:
            ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search([
                    ('giaovien_id', '=', self.giaovien_id.id),
                    ('ngay', '=', self.ngay),
                    ('trangthai', 'in', ['-1','0','1','2','3'])
                ])
            rec.ca2ngay_ids =ca2ngay_ids

    @api.depends("ngay")
    def _compute_name(self):
        for rec in self:
            if rec.ngay:
               rec.name = str(rec.ngay.month) +"/"+ str(rec.ngay.year)
            else:
               today =date.today()
               rec.name = str(today.month) +"/"+ str(today.year)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        if view_type == 'form' and self.env.context.get('params', {}).get('id'):
            record_id = self.env.context['params']['id']


        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            giaovien = None
            if not vals.get('giaovien_id'):
                user = self.env.user
                if user:
                    giaovien = (self.env['ekids.giaovien']
                                .search([('user_id', '=', user.id)], limit=1))
                    if giaovien:
                        vals['giaovien_id'] = giaovien.id
            else:
                giaovien = self.env['ekids.giaovien'].browse(vals.get('giaovien_id'))
            # Tao moi
            ca2ngay = super(GiaoVienChamCong, self).create(vals)
            ca2ngay.func_khoitao_diemdanh_ca2ngay(ca2ngay.ngay, giaovien)
            records.append(ca2ngay)

        return records[0] if len(records) == 1 else records

    def write(self, vals):
        if vals['trangthai'] != '-2':
            vals['xacthuc']='1'
        record = super(GiaoVienChamCong, self).write(vals)
        if record and vals['trangthai'] !='-2':
            self.func_giaovien_vao_xacnhan_chamcong()
        return record
    def func_giaovien_vao_xacnhan_chamcong(self):
        giaovien_id =self.giaovien_id.id
        ngay =self.ngay
        thang = ngay.month
        nam =ngay.year
        day =ngay.day

        giaovien2thang = self.env['ekids.chamcong_giaovien2thang'].search([
            ('giaovien_id', '=', giaovien_id),
            ('chamcong_loai2thang_id.chamcong_loai_id.loai', '=', '0'),
            ('chamcong_loai2thang_id.nam', '=', str(nam)),
            ('chamcong_loai2thang_id.thang', '=', str(thang)),

        ], limit=1)
        if giaovien2thang:
            field = "d"+str(day)
            # chấm công ngày đó nghỉ làm
            setattr(giaovien2thang,field,self.trangthai)





    def func_tao_diemdanh_ca2ngay(self,giaovien_id,ngay):
        hocsinh_ca_canthieps = self.env['ekids.hocsinh_ca_canthiep'].search([
            ('giaovien_id','=',giaovien_id),
            ('hocsinh_id.trangthai', '=', '1'),
            ('hocsinh_id.ngay_nhaphoc', '<=', ngay),
            ('dm_ca_id.trangthai', '=', '1')

        ])
        if hocsinh_ca_canthieps:
            for hocsinh_ca_canthiep in hocsinh_ca_canthieps:
                diemdanh_ca2ngay= self.env['ekids.diemdanh_ca2ngay'].search([
                    ('hocsinh_id', '=', hocsinh_ca_canthiep.hocsinh_id.id),
                    ('ngay', '=', ngay),
                    ('dm_ca_id', '=', hocsinh_ca_canthiep.dm_ca_id.id),
                ],limit=1)



    def action_xacnhan_giaovien_chamcong(self):
            # Lấy giáo viên gắn với user hiện tại
            user = self.env.user
            if user:
                giaovien = (self.env['ekids.giaovien']
                            .search([('user_id', '=', user.id)], limit=1))
                if giaovien:
                    today =date.today()
                    count = self.env['ekids.giaovien_chamcong'].search_count([
                        ('giaovien_id','=',giaovien.id),
                        ('ngay', '=', today),
                    ])
                    if count <= 0:
                        data ={
                            'ngay':today,
                            'giaovien_id':giaovien.id,
                            'trangthai':'-2'
                        }
                        self.env['ekids.giaovien_chamcong'].create(data)

                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'DANH SÁCH XÁC NHẬN',
                        'res_model': 'ekids.giaovien_chamcong',
                        'view_mode': 'list,form',
                        'domain': [('giaovien_id', '=', giaovien.id)],
                        'context': {'default_giaovien_id':giaovien.id},
                        'target': 'current',
                    }


    def action_giaovien_vao_xacnhan_chamcong(self):
        ca2ngay_ids =self.func_khoitao_diemdanh_ca2ngay(self.ngay,self.giaovien_id)
        return {
            'type': 'ir.actions.act_window',
            'name': 'QUAY LẠI -> DANH SÁCH',
            'res_model': 'ekids.giaovien_chamcong',
            'view_mode': 'form',
            'res_id':self.id,
            'target': 'current'
        }





    def func_khoitao_diemdanh_ca2ngay(self,ngay,giaovien):
        diemdanh_ca2ngays = self.env['ekids.diemdanh_ca2ngay'].search([
            ('giaovien_id', '=', giaovien.id),
            ('ngay', '=', ngay),
        ])
        result=[]
        if not diemdanh_ca2ngays:
            result = self.func_tao_macdinh_diemdanh_ca2ngay(ngay,giaovien.id)
        return result

    def func_tao_macdinh_diemdanh_ca2ngay(self,ngay,giaovien_id):

        weekday = ngay.weekday() + 2
        thu_field = 't' + str(weekday)
        ca_canthieps = self.env['ekids.hocsinh_ca_canthiep'].search([
                            ('giaovien_id', '=', giaovien_id),
                            ('hocsinh_id.trangthai', '=', '1'),
                            ('hocsinh_id.ngay_nhaphoc', '<=', ngay),
                            ])
        result =[]
        if ca_canthieps:
            for ca_canthiep in ca_canthieps:
                is_canthiep = getattr(ca_canthiep,thu_field)
                if is_canthiep:
                        count = self.env['ekids.diemdanh_ca2ngay'].search([
                            ('hocsinh_id', '=', ca_canthiep.hocsinh_id.id),
                            ('ngay', '=', ngay),
                            ('hocphi_dm_ca_id', '=', ca_canthiep.dm_ca_id.id),
                        ])
                        if count <=0:
                            data={
                                'hocphi_dm_ca_id': ca_canthiep.dm_ca_id.id,
                                'ngay': ngay,
                                'tu': ca_canthiep.tu,
                                'den': ca_canthiep.den,
                                'hocsinh_id': ca_canthiep.hocsinh_id.id,
                                'giaovien_id': giaovien_id,
                                'trangthai': '0',

                            }
                            ca2ngay =self.env['ekids.diemdanh_ca2ngay'].create(data)
                            result.append(ca2ngay)
        return result


    def action_open_popup_tao_diemdanh_ca2ngay_hocbu(self):
        user = self.env.user
        if user:
            giaovien = (self.env['ekids.giaovien']
                        .search([('user_id', '=', user.id)], limit=1))
            if giaovien:
                form_view_id =self.env.ref('ekids_giaovien_myprofile.diemdanh_ca2ngay_wizard_form_inherit').id
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Điểm danh ngày',
                    'res_model': 'ekids.diemdanh_ca2ngay_wizard',
                    'view_mode': 'form',
                    'views': [(form_view_id, 'form')],
                    'target': 'new',
                    'context':
                        {
                            'default_coso_id': giaovien.coso_id.id,
                            'default_giaovien_id': giaovien.id,
                            'default_ngay': self.ngay

                         }
                }










