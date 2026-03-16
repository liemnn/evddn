from datetime import datetime, timedelta,date
from . import  coso_util,ngay_util
from odoo.osv import expression
def func_get_nghipheps_trong_khoang_thoigian(self,coso, hocsinh, nghiles,nhatruong_nghis, tu_ngay, den_ngay):
    nghipheps = self.env['ekids.hocsinh_nghiphep'].search([
        ('hocsinh_id', '=', hocsinh.id),
        ('tu_ngay', '<=', den_ngay),
        ('den_ngay', '>=', tu_ngay),
    ])

    days = {}
    # B1: So ngay di hoc mac dinh trong thang chua tinh nghi le
    if nghipheps:
        for nghiphep in nghipheps:
            ngay_start = nghiphep.tu_ngay
            ngay_end = nghiphep.den_ngay
            if ngay_start < tu_ngay:
                ngay_start = tu_ngay
            if ngay_end > den_ngay:
                ngay_end = den_ngay

            ngay = ngay_start
            while ngay <= ngay_end:
                if coso_util.func_is_coso_hoatdong(coso, ngay):
                    key = str(ngay)
                    if (nghiles
                            and len(nghiles)>0
                            and nghiles.get(key)):
                        ngay += timedelta(days=1)
                        continue
                    elif(nhatruong_nghis
                          and len(nhatruong_nghis)>0
                          and nhatruong_nghis.get(key)):
                            ngay += timedelta(days=1)
                            continue
                    else:
                        days[key] = nghiphep
                ngay += timedelta(days=1)
    return days

def func_get_nghipheps_tatca_hocsinh(self, coso,nam,thang):
    result={}
    days = ngay_util.func_get_cacngay_trong_thang(nam, thang)
    ngay_dauthang= days[0]
    ngay_cuoithang=days[len(days)-1]
    nghipheps = self.env['ekids.hocsinh_nghiphep'].search([
        ('coso_id', '=', coso.id),
        ('tu_ngay', '<=', ngay_cuoithang),
        ('den_ngay', '>=', ngay_dauthang),
    ])
    for day in days:
        for nghiphep in nghipheps:
            key = str(nghiphep.hocsinh_id.id)+":" +str(day)
            if  day >= nghiphep.tu_ngay and day <= nghiphep.den_ngay:
                result[key] = nghiphep
            else:
                continue
    return result

def func_get_ngay_dihoc_kehoachs(coso, nghiles,hocsinh,tu_ngay, den_ngay):
    ngay = tu_ngay
    days = {}
    if hocsinh.ngay_nhaphoc > tu_ngay:
        ngay = hocsinh.ngay_nhaphoc

    if  (hocsinh.trangthai == '3'
        and hocsinh.ngay_nghihoc
             and hocsinh.ngay_nghihoc < den_ngay):
        den_ngay = hocsinh.ngay_nghihoc

    while ngay <= den_ngay:
        is_coso_hoatdong = coso_util.func_is_coso_hoatdong(coso, ngay)
        if is_coso_hoatdong:
            # Co so hoat dong
            if nghiles:
                is_nghile = nghiles.get(str(ngay), False)
                if is_nghile == False:
                    is_hoc = func_is_co_ca_trong_ngay(hocsinh, ngay)
                    if is_hoc == True:
                        days[str(ngay)] = ngay
            else:
                is_hoc =func_is_co_ca_trong_ngay(hocsinh,ngay)
                if is_hoc == True:
                    days[str(ngay)] = ngay

        ngay += timedelta(days=1)
    return days
def func_get_ngay_dihoc_cua_coso(coso, nghiles,tu_ngay, den_ngay):
    ngay = tu_ngay
    days = {}
    while ngay <= den_ngay:
        is_coso_hoatdong = coso_util.func_is_coso_hoatdong(coso, ngay)
        if is_coso_hoatdong:
            # Co so hoat dong
            days[str(ngay)] = ngay
            """
            if nghiles:
                is_nghile = nghiles.get(str(ngay), False)
                if is_nghile == False:
                    days[str(ngay)] = ngay
            else:
               days[str(ngay)] = ngay
            """

        ngay += timedelta(days=1)
    return days


def func_is_co_ca_trong_ngay(hocsinh,ngay):
    week = ngay.weekday() + 2
    field_name = "hd_t" + str(week)
    if hocsinh.is_ngaydihoc_rieng ==True:
        is_hoc = getattr(hocsinh,field_name)
        if is_hoc == True:
            return True
    else:
        coso =hocsinh.coso_id
        is_hoc = getattr(coso, field_name)
        if is_hoc == True:
            return True
    return False


def func_get_ngay_dihoc_thucte(self,hocsinh2thang, nghiles):

    result = {}
    nam = int(hocsinh2thang.diemdanh_id.nam)
    thang = int(hocsinh2thang.diemdanh_id.thang)
    days = ngay_util.func_get_cacngay_trong_thang(nam,thang)
    ngay_dauthang = days[0]
    ngay_cuoithang = days[len(days)-1]
    if ngay_dauthang < hocsinh2thang.hocsinh_id.ngay_nhaphoc:
        ngay_dauthang = hocsinh2thang.hocsinh_id.ngay_nhaphoc
    nghipheps = func_get_nghipheps_trong_khoang_thoigian(self,hocsinh2thang.coso_id, hocsinh2thang.hocsinh_id, nghiles,None, ngay_dauthang, ngay_cuoithang)
    ngay =ngay_dauthang
    while ngay <= ngay_cuoithang:
        is_hoatdong = coso_util.func_is_coso_hoatdong(hocsinh2thang.coso_id,ngay)
        if is_hoatdong == True:
            if not nghiles.get(str(ngay)):
                if not nghipheps.get(str(ngay)):
                    field_name = "d"+str(ngay.day)
                    giatri =getattr(hocsinh2thang,field_name,'-1')
                    if giatri == '1' or giatri == '11':
                        result[str(ngay)] =ngay
        ngay += timedelta(days=1)
    return result



def func_get_cas_tangcuong_tatca_hocsinh(self, coso,nam,thang):
    result={}
    days = ngay_util.func_get_cacngay_trong_thang(nam, thang)
    ngay_dauthang= days[0]
    ngay_cuoithang=days[len(days)-1]
    ca_tangcuongs = self.env['ekids.diemdanh_ca2ngay'].search([
        ('coso_id', '=', coso.id),
        ('ngay', '>=', ngay_dauthang),
        ('ngay', '<=', ngay_cuoithang),
        ('trangthai', 'in', ['4', '5']) # 4: đã dạy bù, 5: tăng cường
    ])
    if ca_tangcuongs:
        for ca_tangcuong in ca_tangcuongs:
            key = str(ca_tangcuong.hocsinh_id.id)+":" +str(ca_tangcuong.ngay)
            result[key] = ca_tangcuong

    return result



def func_get_tinhtoan_ca2thu_theo_thu(self,hocsinh,day):
    weekday = day.weekday() + 2
    tinhtoan_ca2thus = self.env['ekids.tinhtoan_ca2thu'].search([
        ('hocsinh_id', '=',hocsinh.id),
        ('thu', '=', weekday),
    ])
    return tinhtoan_ca2thus

def func_get_so_hocsinh_trong_thang(self,coso_id,nam,thang):
    domain = func_get_domain_trong_thang(coso_id, nam, thang)
    count = self.env['ekids.hocsinh'].search_count(domain)

    if count:
        return count
    else:
        return 0

def func_get_hocsinhs_trong_thang(self, coso_id, nam, thang):
    domain =func_get_domain_trong_thang(coso_id,nam,thang)

    hocsinhs = self.env['ekids.hocsinh'].search(domain)

    return hocsinhs

def func_get_domain_trong_thang(coso_id, nam, thang):
    days = ngay_util.func_get_cacngay_trong_thang(int(nam), int(thang))
    ngay_dauthang = days[0]
    ngay_cuoithang = days[len(days) - 1]

    domain_chung= [
        ('coso_id', '=', coso_id),
        ('ngay_nhaphoc', '<=', ngay_cuoithang),
    ]

    # Nhóm 1: Học sinh đang theo học
    domain_theohoc = [
        ('trangthai', '=', '1'),
    ]

    # Nhóm 2: Học sinh đã nghỉ nhưng nghỉ trong tháng tìm kiếm
    domain_danghi = [
        ('trangthai', '=', '3'),
        ('ngay_nghihoc', '!=', False),
        ('ngay_nghihoc', '>=', ngay_dauthang),
        ('ngay_nghihoc', '<=', ngay_cuoithang),
    ]

    domain = expression.AND([
        domain_chung,
        expression.OR([
            domain_theohoc,
            domain_danghi
        ])
    ])

    return domain

