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
                    if hocsinh.is_ngaydihoc_rieng == True:
                        week = ngay.weekday() + 2
                        field_name = "hd_t" + str(week)
                        is_hoc = getattr(hocsinh, field_name)
                        if is_hoc == False:
                            ngay += timedelta(days=1)
                            continue
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
            #days[str(ngay)] = ngay

            if nghiles:
                is_nghile = nghiles.get(str(ngay))
                if not is_nghile:
                    days[str(ngay)] = ngay
            else:
               days[str(ngay)] = ngay


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
    days = ngay_util.func_get_cacngay_trong_thang(int(nam), int(thang))
    tu_ngay = days[0]
    den_ngay = days[len(days) - 1]
    coso_ids = [coso_id]

    domain = func_get_domain_trong_khoang_thoigian(coso_ids, tu_ngay, den_ngay)

    count = self.env['ekids.hocsinh'].search_count(domain)

    if count:
        return count
    else:
        return 0



def func_danhsach_hocsinh_trongthang(self, coso_id, nam, thang):
    days = ngay_util.func_get_cacngay_trong_thang(int(nam), int(thang))
    tu_ngay = days[0]
    den_ngay = days[len(days) - 1]
    coso_ids = [coso_id]

    domain =func_get_domain_trong_khoang_thoigian(coso_ids,tu_ngay,den_ngay)

    hocsinhs = self.env['ekids.hocsinh'].search(domain)

    return hocsinhs

def func_danhsach_hocsinh_khoang_thoigian(self, coso_ids, tu_ngay, den_ngay):

    domain =func_get_domain_trong_khoang_thoigian(coso_ids,tu_ngay,den_ngay)

    hocsinhs = self.env['ekids.hocsinh'].search(domain)

    return hocsinhs




def func_get_domain_trong_khoang_thoigian(coso_ids, tu_ngay,den_ngay):

    domain_chung= [
        ('coso_id', 'in', coso_ids),
        ('ngay_nhaphoc', '<=', den_ngay),
    ]

    # Nhóm 1: Học sinh đang theo học
    domain_theohoc = [
        ('trangthai', '=', '1'),
    ]

    # Nhóm 2: Học sinh đã nghỉ nhưng nghỉ trong tháng tìm kiếm
    domain_danghi = [
        ('trangthai', '=', '3'),
        ('ngay_nghihoc', '!=', False),
        ('ngay_nghihoc', '>=', tu_ngay),
        ('ngay_nghihoc', '<=', den_ngay),
    ]

    domain = expression.AND([
        domain_chung,
        expression.OR([
            domain_theohoc,
            domain_danghi
        ])
    ])

    return domain


def func_is_hoc(self, hocsinh, ngay):
    # Tránh lỗi nếu biến ngay hoặc ngay_nhaphoc bị trống (False/None) dưới database
    if not ngay or not hocsinh.ngay_nhaphoc:
        return False
    # ngày tương lại không học
    today = date.today()
    if ngay > today:
        return False

    # 1. KIỂM TRA THEO TRẠNG THÁI HIỆN TẠI TRÊN HỒ SƠ
    # Điều kiện cần: Ngày xét phải từ ngày nhập học trở đi

    if ngay >= hocsinh.ngay_nhaphoc:
        # Trường hợp 1: Học sinh vẫn đang học (chưa có ngày nghỉ học chính thức)
        if not hocsinh.ngay_nghihoc:
            return True
        # Trường hợp 2: Học sinh đã nghỉ học, nhưng ngày xét nằm trước hoặc đúng ngày nghỉ
        else:  # Đã sửa lỗi thiếu dấu : ở đây
            if ngay <= hocsinh.ngay_nghihoc:
                return True

    # 2. KIỂM TRA TRONG LỊCH SỬ CAN THIỆP (Nếu không thỏa mãn điều kiện hiện tại)
    # Tối ưu: Đẩy thẳng điều kiện ngày xuống Database thông qua Domain của Odoo
    # Dùng search_count để kiểm tra số lượng bản ghi, tránh kéo data thô lên RAM làm chậm server
    lichsu_count = self.env['ekids.hocsinh_lichsu_canthiep'].search_count([
        ('hocsinh_id', '=', hocsinh.id),
        ('tu_ngay', '<=', ngay),
        ('den_ngay', '>=', ngay)
    ])

    if lichsu_count > 0:
        return True

    # Không nằm trong bất kỳ khoảng thời gian đi học nào
    return False


