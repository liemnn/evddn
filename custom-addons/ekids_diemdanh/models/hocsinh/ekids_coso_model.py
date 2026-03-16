from odoo import models, fields, api, _
from datetime import datetime
from datetime import date

from odoo.exceptions import UserError

class CoSo(models.Model):
    _inherit = "ekids.coso"

    def action_quanly_nghiphep_hocsinh(self):
        list_view_id = self.env.ref('ekids_diemdanh.hocsinh_nghiphep_list').id
        form_view_id = self.env.ref('ekids_diemdanh.hocsinh_nghiphep_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'NGHỈ PHÉP',
            'res_model': 'ekids.hocsinh_nghiphep',
            'view_mode': 'list,form',
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_xem_toanbo_diemdanh_thang(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'THÁNG ĐIỂM DANH',
            'res_model': 'ekids.diemdanh',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id
            }
        }
    def action_diemdanh_thang_nay(self):
        today = date.today()
        diemdanh =self.func_tao_macdinh_diemdanh_thang(today.year,today.month)
        if diemdanh:
            name ='THÁNG '+str(today.month)+"/" +str(today.year)
            return {
                'type': 'ir.actions.act_window',
                'name': name,
                'res_model': 'ekids.diemdanh_hocsinh2thang',
                'view_mode': 'list',
                'target': 'current',
                'domain': [
                    ('coso_id', '=', self.id),
                    ('diemdanh_id','=',diemdanh.id)
                ],
                'context': {
                    'default_coso_id': self.id,
                    'default_thang': str(today.month),
                    'default_nam': str(today.year)
                }
            }


    def func_tao_macdinh_diemdanh_thang(self,nam,thang):

        diemdanh = self.env['ekids.diemdanh'].search([
            ('coso_id', '=', self.id)
            , ('nam', '=', str(nam))
            , ('thang', '=', str(thang))
        ], limit=1)

        if not diemdanh:
            data = {
                'coso_id': self.id,
                'nam': str(nam),
                'thang': str(thang)
            }
            diemdanh = self.env['ekids.diemdanh'].create(data)
        diemdanh.func_tao_macdinh_diemdanh_hocsinh2thang()
        return  diemdanh

    def action_diemdanh_ngay_homnay(self):
        today = date.today()
        is_hoatdong = self.func_is_ngay_trong_thang_hoatdong(today.day,today.month,today.year,self)
        if is_hoatdong:
            self.func_tao_diemdanh_default_today()

            return {
                'type': 'ir.actions.act_window',
                'name': 'ĐIỂM DANH HÔM NAY['+str(today)+']',
                'res_model': 'ekids.diemdanh_ngay',
                'view_mode': 'kanban,list',
                'target': 'current',
                'domain': [('coso_id', '=', self.id),('ngay','=',today)],
                'context': {
                    'default_coso_id': self.id
                }
            }
        else:
            raise UserError("Không thể thực hiện [Điểm danh] hôm nay vì là ngày nghỉ của Cơ  sở !")

    def func_tao_diemdanh_default_today(self):
        today = date.today()
        month = today.month
        year =today.year
        ngay_dau_thang_nay = date(int(year), int(month), 1)

        hocsinhs = self.env['ekids.hocsinh'].search(
            [
                ('coso_id', '=', self.id),
                ('trangthai', '=', '1'),
                ('ngay_nhaphoc', '<=', ngay_dau_thang_nay)
            ])
        if hocsinhs:
            for hs in hocsinhs:

                count = self.env['ekids.diemdanh_ngay'].search_count([
                        ('coso_id', '=', self.id),
                        ('hocsinh_id', '=', hs.id),
                        ('ngay', '=', today)

                        ],limit=1)
                if count<=0:
                    data = {
                        'coso_id': self.id,
                        'hocsinh_id': hs.id,
                        'ngay': today,
                        'trangthai':'0'

                    }
                    diemdanh_ngay =self.env['ekids.diemdanh_ngay'].create(data)
                    diemdanh_ngay.func_capnhat_bang_diemdanh_thang_tu_diemdanh_ngay(diemdanh_ngay.ngay,hs.id,'0')
