from datetime import datetime, timedelta,date
from odoo.osv import expression

from . import  giaovien_util

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



MUCTIEU_SOLUONG_MO="muctieu_soluong_mo"


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
def func_get_kehoach_hocsinh_gannhat(self, hocsinh):
    giaovien =giaovien_util.func_get_giaovien_tu_user(self)
    if giaovien:

        kehoach_gan_nhat = (self.env['ekids.kehoach']
                            .search([("hocsinh_id","=",hocsinh.id),("gv_lapkehoach_id","=",giaovien.id)], order='den_ngay desc', limit=1))
        return kehoach_gan_nhat
    else:
        return None

def func_get_kehoach_hocsinh_trangthai(self, hocsinh, trangthais):
    return func_get_kehoach_hocsinh_trangthai_ngay(self, hocsinh, trangthais,None)




def func_get_kehoach_hocsinh_trangthai_ngay(self, hocsinh, trangthais,ngay):
    giaovien =giaovien_util.func_get_giaovien_tu_user(self)
    if giaovien:
        domain =[ ('hocsinh_id', '=', hocsinh.id),
                  ('gv_lapkehoach_id', '=', giaovien.id),
                    ('trangthai', 'in', trangthais)]
        if ngay:
            domain.append(("tu_ngay","<=",ngay))
            domain.append(("den_ngay", ">=", ngay))

        kehoach = self.env['ekids.kehoach'].search(domain
            , order="id desc", limit=1)
        return kehoach
    else:
        return None

def func_get_kehoach_can_canthiep_ocsinh_trangthai_ngay(self, hocsinh, trangthais,ngay):
    giaovien =giaovien_util.func_get_giaovien_tu_user(self)
    if giaovien:
        domain =[ ('hocsinh_id', '=', hocsinh.id),
                    ('trangthai', 'in', trangthais)]
        if ngay:
            domain.append(("tu_ngay","<=",ngay))
            domain.append(("den_ngay", ">=", ngay))

        if giaovien:
            domain_lap =[('gv_lapkehoach_id', '=', giaovien.id)]
            domain_kiemduyet = [('ketluan_id.gv_kiemduyet_id', '=', giaovien.id)]
            domain_gv = expression.OR([domain_lap, domain_kiemduyet])
            domain = expression.AND([domain, domain_gv])



        kehoach = self.env['ekids.kehoach'].search(domain
            , order="id desc", limit=1)
        return kehoach
    else:
        return None


def func_get_kehoach_can_kiemduyet_hocsinh_trangthai(self, hocsinh, trangthais):
    giaovien = giaovien_util.func_get_giaovien_tu_user(self)
    if giaovien:
        domain = [('hocsinh_id', '=', hocsinh.id),
                  ('ketluan_id.gv_kiemduyet_id', '=', giaovien.id),
                  ('trangthai', 'in', trangthais)]


        kehoach = self.env['ekids.kehoach'].search(domain
                                                   , order="id desc", limit=1)
        return kehoach
    else:
        return None





def func_count_kehoach_hocsinh_trangthai(self, hocsinh, trangthais):
    giaovien = giaovien_util.func_get_giaovien_tu_user(self)
    if giaovien:
        count = self.env['ekids.kehoach'].search_count([
            ('hocsinh_id', '=', hocsinh.id),
            ('trangthai', 'in', trangthais),
            ('gv_lapkehoach_id', '=', giaovien.id),
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

        domain_duyet = [('gv_kiemduyet_id', '=', giaovien.id)]
        domain_canthiep = [('gv_canthiep_ids', 'in', [giaovien.id])]

        # 2. Gộp chúng lại bằng expression.OR (nhận vào một mảng chứa các domain)
        domain = expression.OR([domain_duyet, domain_canthiep])

        # 3. Tìm kiếm
        kehoachs = self.env['ekids.kehoach_ketluan'].search(domain)
        if kehoachs:
            hocsinh_ids=[]
            for kh in kehoachs:
                hocsinh_ids.append(kh.hocsinh_id.id)
            return hocsinh_ids
    return None


def func_get_ids_hocsinh_theo_vaitro_lap_kehoach(self):
    user = self.env.user
    giaovien = giaovien_util.func_get_giaovien_tu_user(self)
    if giaovien:
        # 1. Khai báo các điều kiện độc lập cho rõ ràng
        domain = [('gv_canthiep_ids', 'in', [giaovien.id])
            ,('trangthai', 'in', ['1','-1'])]


        # 3. Tìm kiếm
        ketluans = self.env['ekids.kehoach_ketluan'].search(domain)
        if ketluans:
            hocsinh_ids=[]
            for kl in ketluans:
                hocsinh_ids.append(kl.hocsinh_id.id)
            return hocsinh_ids
    return None

def func_get_ids_hocsinh_theo_vaitro_duyet_kehoach(self):
    giaovien = giaovien_util.func_get_giaovien_tu_user(self)
    if giaovien:
        # 1. Khai báo các điều kiện độc lập cho rõ ràng
        domain = [("ketluan_id.gv_kiemduyet_id","=", giaovien.id)
            ,("ketluan_id.trangthai",'in', ['1', '-1'])]

        # 3. Tìm kiếm
        kehoachs = self.env['ekids.kehoach'].search(domain)
        if kehoachs:
            hocsinh_ids = []
            for kl in kehoachs:
                hocsinh_ids.append(kl.hocsinh_id.id)
            return hocsinh_ids
    return None

def func_get_ids_hocsinh_theo_vaitro_canthiep_kehoach(self):
    giaovien =giaovien_util.func_get_giaovien_tu_user(self)
    if giaovien:
        #TH1:
        # 1. Khai báo các điều kiện độc lập cho rõ ràng
        domain = [('gv_lapkehoach_id', '=', giaovien.id)]

        # 3. Tìm kiếm
        kehoachs = self.env['ekids.kehoach'].search(domain)
        if kehoachs:
            hocsinh_ids = []
            for kh in kehoachs:
                hocsinh_ids.append(kh.hocsinh_id.id)
            return hocsinh_ids
    return None





