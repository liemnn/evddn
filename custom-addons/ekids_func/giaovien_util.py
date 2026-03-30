from datetime import datetime, timedelta,date
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
from . import  coso_util,ngay_util
from odoo.osv import expression
def func_get_nghipheps_trong_khoang_thoigian(self,coso, giaovien, nghiles, loai,tu_ngay, den_ngay):
    domain =[
                ('giaovien_id', '=', giaovien.id),
                ('tu_ngay', '<=', den_ngay),
                ('den_ngay', '>=', tu_ngay),
            ]
    if loai:
        domain.append(('loai','=',loai))
    nghipheps = self.env['ekids.giaovien_nghiphep'].search(domain)

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
                key = str(ngay)
                if coso_util.func_is_coso_hoatdong(coso, ngay):
                    if nghiles.get(key):
                        ngay += timedelta(days=1)
                        continue
                    else:
                        days[key] = nghiphep
                ngay += timedelta(days=1)
    return days

def func_get_nghipheps_tatca_giaovien(self, coso,nam,thang):
    result={}
    days = ngay_util.func_get_cacngay_trong_thang(nam, thang)
    ngay_dauthang= days[0]
    ngay_cuoithang=days[len(days)-1]
    nghipheps = self.env['ekids.giaovien_nghiphep'].search([
        ('coso_id', '=', coso.id),
        ('tu_ngay', '<=', ngay_cuoithang),
        ('den_ngay', '>=', ngay_dauthang),
    ])
    for day in days:
        for nghiphep in nghipheps:
            key = str(nghiphep.giaovien_id.id)+":" +str(day)
            if  day >= nghiphep.tu_ngay and day <= nghiphep.den_ngay:
                result[key] = nghiphep
            else:
                continue
    return result

def func_get_ngay_dilam_theo_kehoach(self, coso,nghiles,tu_ngay, den_ngay):

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
                if not is_nghile:
                    days[str(ngay)] = ngay
            else:
                days[str(ngay)] = ngay
            """

        ngay += timedelta(days=1)
    return days

def func_get_dulieu_chamcong_thucte_giaovien(self,coso_dilam_kehoachs,giaovien,nghiles,nghipheps,nam,thang):
    giaovien2thang = func_get_chamcong_giaovien2thang(self,giaovien, nam, thang)
    #TH1: đi lam ca ngay = di lam dung gio + di lam muon ( di ca ngay)
    dilam_cangay =  func_get_ngays_theloai_trong_khoang_thoigian(self, giaovien2thang, ['1','10'],
                                                                                        nghiles, nghipheps,
                                                                                        coso_dilam_kehoachs)
    dilam_nuabuoi = func_get_ngays_theloai_trong_khoang_thoigian(self, giaovien2thang, ['0', '00'],
                                                                          nghiles, nghipheps,
                                                                          coso_dilam_kehoachs)

    dilam_muon = func_get_ngays_theloai_trong_khoang_thoigian(self, giaovien2thang, ['10','00'],
                                                                                       nghiles, nghipheps,
                                                                                       coso_dilam_kehoachs)

    chamcong_nghi = func_get_ngays_theloai_trong_khoang_thoigian(self, giaovien2thang, ['-1'],
                                                                                    nghiles, nghipheps,
                                                                                    coso_dilam_kehoachs)
    dilam_nghi_giua_thang = func_get_songay_dilam_hoac_nghi_giua_thang(giaovien2thang.giaovien_id,coso_dilam_kehoachs)


    duoc_chamcong = len(dilam_cangay)  + (len(dilam_nuabuoi) * 0.5)
    nghi = len(chamcong_nghi) + int(dilam_nghi_giua_thang)
    data ={
        'dilam_muon':len(dilam_muon),
        'dilam_nuabuoi':len(dilam_nuabuoi),
        'dilam_nghi':nghi,
        'dilam_chamcong':duoc_chamcong
    }

    return data

def func_get_songay_dilam_hoac_nghi_giua_thang(giaovien,dilam_kehoachs):
    ngay = 0
    if dilam_kehoachs:
        for key in dilam_kehoachs:
            day = dilam_kehoachs.get(key)
            if day:
                if (giaovien.dilam_tungay and day < giaovien.dilam_tungay):
                   ngay = ngay +1

                if (giaovien.trangthai =='0'
                        and giaovien.dilam_denngay
                        and day > giaovien.dilam_denngay):
                   ngay = ngay +1

                if giaovien.is_ngaydilam_rieng == True:
                    #thiết lập ngày đi làm riêng
                    week = day.weekday() + 2
                    field_name = "hd_t" + str(week)
                    is_dilam = getattr(giaovien, field_name)
                    if is_dilam == False:
                        ngay = ngay +1
    return ngay

def func_get_chamcong_giaovien2thang(self,giaovien,nam,thang):
    chamcong = self.env['ekids.chamcong_giaovien2thang'].search([
        ('giaovien_id', '=', giaovien.id),
        ('chamcong_loai2thang_id.thang', '=', str(thang)),
        ('chamcong_loai2thang_id.nam', '=', str(nam)),
    ],limit=1)
    return chamcong

def func_get_ngays_theloai_trong_khoang_thoigian(self,chamcong,theloais,nghiles, nghipheps,dilam_kehoachs):
    days = {}

    if chamcong:
        giaovien =chamcong.giaovien_id
        for key in dilam_kehoachs:
            day = dilam_kehoachs.get(key)
            if day <giaovien.dilam_tungay:
                continue
            dayofmonth = day.day
            field_day = 'd' + str(dayofmonth)
            giatri = getattr(chamcong, field_day)
            if giatri in theloais:
                # đi làm hoặc có đi làm nhưng đi làm muộn
                # không dược điểm danh do nghỉ
                nghile = nghiles.get(key)
                nghiphep = nghipheps.get(key)
                if nghile:
                    continue
                elif nghiphep:
                    if nghiphep.loai == '1':
                        # ngay bị tru luong
                        continue
                    else:
                        days[key] = day
                else:
                    days[key] = day

    return days

def func_get_thamnien(giaovien):
    today = date.today()
    if not giaovien.dilam_tungay:
        return 0.0

    diff = relativedelta(today, giaovien.dilam_tungay)
    # số năm + (số tháng / 12)
    result = diff.years + diff.months / 12.0
    return round(result, 1)   # làm tròn 1 chữ số thập phân



def func_get_giaoviens_trong_thang(self, coso_id, nam, thang):
    domain =func_get_domain_trong_thang(coso_id,nam,thang)

    giaoviens = self.env['ekids.giaovien'].search(domain)

    return giaoviens

def func_get_domain_trong_thang(coso_id, nam, thang):
    days = ngay_util.func_get_cacngay_trong_thang(int(nam), int(thang))
    ngay_dauthang = days[0]
    ngay_cuoithang = days[len(days) - 1]

    domain_chung= [
        ('coso_id', '=', coso_id),
        ('dilam_tungay', '<=', ngay_cuoithang),
    ]

    # Nhóm 1: giáo viên đang làm việc
    domain_theohoc = [
        ('trangthai', '=', '1'),
    ]

    # Nhóm 2: giáo viên đã nghỉ việc nhưng vẫn được tính lương trong tháng, hoc giáo viên =2: Nghi thai sản
    domain_danghi = [
        ('trangthai', 'in', ['0','2']),
        ('dilam_denngay', '!=', False),
        ('dilam_denngay', '>=', ngay_dauthang),
        ('dilam_denngay', '<=', ngay_cuoithang),
    ]

    domain = expression.AND([
        domain_chung,
        expression.OR([
            domain_theohoc,
            domain_danghi
        ])
    ])

    return domain




