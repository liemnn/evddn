from datetime import datetime, timedelta,date
from odoo.osv import expression

KETLUAN_CHUA_CO='-2'
KETLUAN_DANG_TAO='0'
KETLUAN_CHOPHEP_LAP_KEHOACH='1'
KETLUAN_HET_HIEULUC='-1'

KEHOACH_DANG_LAP='0'
KEHOACH_DANG_PHEDUYET='2'
KEHOACH_DANG_CANTHIEP='1'
KEHOACH_HET_HIEULUC="-1"

PHEDUYET_DOI_DUYET="0"
PHEDUYET_CAN_DIEUCHINH="-1"
PHEDUYET_DA_DUYET="1"



HOCSINH_CHUA_CO_KEHOACH="-2"
HOCSINH_DANG_LAP_KEHOACH="0"
HOCSINH_DANG_CANTHIEP="1"
HOCSINH_HET_HIEULUC="-1"
HOCSINH_DA_DUYET="3"
HOCSINH_DOI_DUYET="4"
HOCSINH_CAN_DIEUCHINH="-3"


def func_get_ketluan_hocsinh(self, hocsinh):
    ketluan = self.env['ekids.kehoach_ketluan'].search([
        ('hocsinh_id', '=', hocsinh.id),
    ]
        , order="id desc", limit=1)
    return ketluan


def func_get_ketluan_hocsinh_trangthai(self, hocsinh, trangthais):
    ketluan = self.env['ekids.kehoach_ketluan'].search([
        ('hocsinh_id', '=', hocsinh.id),
        ('trangthai', 'in', trangthais),
    ]
        , order="id desc", limit=1)
    return ketluan

def func_count_ketluan_hocsinh_trangthai(self, hocsinh, trangthais):
    count = self.env['ekids.kehoach_ketluan'].search_count ([
        ('hocsinh_id', '=', hocsinh.id),
        ('trangthai', 'in', trangthais),
    ])
    return count


def func_get_kehoach_hocsinh(self, hocsinh):
    kehoach = self.env['ekids.kehoach'].search([
        ('hocsinh_id', '=', hocsinh.id),
    ]
        , order="id desc", limit=1)
    return kehoach


def func_get_kehoach_hocsinh_trangthai(self, hocsinh, trangthais):
    kehoach = self.env['ekids.kehoach'].search([
        ('hocsinh_id', '=', hocsinh.id),
        ('trangthai', 'in', trangthais),
    ]
        , order="id desc", limit=1)
    return kehoach

def func_count_kehoach_hocsinh_trangthai(self, hocsinh, trangthais):
    count = self.env['ekids.kehoach'].search_count([
        ('hocsinh_id', '=', hocsinh.id),
        ('trangthai', 'in', trangthais),
    ])
    return count



def func_get_ids_hocsinh_theo_vaitro(self):
    user = self.env.user
    is_admin = user.has_group('base.group_system')
    is_role_ketluan = user.has_group('ekids_core.ketluan')

    if is_admin or is_role_ketluan:
        return None


    giaovien = (self.env['ekids.giaovien']
                .search([('user_id', '=', user.id)], limit=1))
    if giaovien:
        # 1. Khai báo các điều kiện độc lập cho rõ ràng
        domain_lap = [('gv_lapkehoach_id', '=', giaovien.id)]
        domain_duyet = [('gv_kiemduyet_id', '=', giaovien.id)]
        domain_canthiep = [('gv_canthiep_id', '=', giaovien.id)]

        # 2. Gộp chúng lại bằng expression.OR (nhận vào một mảng chứa các domain)
        domain = expression.OR([domain_lap, domain_duyet, domain_canthiep])

        # 3. Tìm kiếm
        kehoachs = self.env['ekids.kehoach_ketluan'].search(domain)
        if kehoachs:
            hocsinh_ids=[]
            for kh in kehoachs:
                hocsinh_ids.append(kh.hocsinh_id.id)
            return hocsinh_ids
    return None






