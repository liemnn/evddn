from odoo import models, fields, api, _
from datetime import datetime
from odoo.osv import expression
from datetime import date

from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")


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
            domain  = self.func_get_domain_trong_khoang_thoigian_diemdanh(diemdanh)
            return {
                'type': 'ir.actions.act_window',
                'name': name,
                'res_model': 'ekids.diemdanh_hocsinh2thang',
                'view_mode': 'list',
                'target': 'current',
                'domain':domain,
                'context': {
                    'default_coso_id': self.id,
                    'default_thang': str(today.month),
                    'default_nam': str(today.year)
                }
            }

    def func_xoa_diemdanh_khi_hocsinh_nghi_trongthang(self,diemdanh):
        hocsinh2thang_ids = diemdanh.hocsinh2thang_ids
        if hocsinh2thang_ids:
            today = date.today()
            thang = today.month
            nam = today.year
            ngays = ngay_util.func_get_cacngay_trong_thang(nam, thang)
            tu_ngay = ngays[0]

            for hocsinh2thang in hocsinh2thang_ids:
                ngay_nghihoc = hocsinh2thang.hocsinh_id.ngay_nghihoc
                if ngay_nghihoc:
                    if ngay_nghihoc < tu_ngay:
                        hocsinh2thang.unlink()

    def func_get_domain_trong_khoang_thoigian_diemdanh(self,diemdanh):
        today = date.today()
        thang =today.month
        nam = today.year
        ngays = ngay_util.func_get_cacngay_trong_thang(nam, thang)
        tu_ngay = ngays[0]
        den_ngay = ngays[len(ngays) - 1]

        self.func_xoa_diemdanh_khi_hocsinh_nghi_trongthang(diemdanh)

        domain_chung = [('coso_id', '=', self.id),
                       ('diemdanh_id', '=', diemdanh.id),
                    ('hocsinh_id.ngay_nhaphoc', '<=', den_ngay)
                 ]



        # Nhóm 1: Học sinh đang theo học
        domain_theohoc = [
            ('hocsinh_id.trangthai', '=', '1'),
        ]

        # Nhóm 2: Học sinh đã nghỉ nhưng nghỉ trong tháng tìm kiếm
        domain_danghi = [
            ('hocsinh_id.ngay_nghihoc', '!=', False),
            ('hocsinh_id.ngay_nghihoc', '>=', tu_ngay)
        ]


        domain = expression.AND([
            domain_chung,
            expression.OR([
                domain_theohoc,
                domain_danghi
            ])
        ])

        return domain


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



