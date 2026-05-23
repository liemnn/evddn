from datetime import datetime, timedelta,date
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
from . import  coso_util,ngay_util,string_util
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
                is_dilam = func_is_dilam_trong_ngay(giaovien, ngay)
                if is_dilam == True:
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

def func_get_giaovien_ngay_dilam_theo_kehoach(self, coso,giaovien,nghiles,tu_ngay, den_ngay):

    datas = func_get_ngay_dilam_theo_kehoach(self, coso,nghiles,tu_ngay, den_ngay)
    if giaovien.is_ngaydilam_rieng == False:
        return datas
    else:
        days = {}
        if datas:
            for key in datas:
                day = string_util.string2date(key)
                is_dilam = func_is_dilam_trong_ngay(giaovien,day)
                if is_dilam == True:
                    days[key] = datas[key]


        return days

def func_get_dulieu_chamcong_thucte_giaovien(self
                                             ,coso_dilam_kehoachs
                                             ,giaovien
                                             ,nghiles
                                             ,coso_chonghi_truluongs
                                             ,nghipheps
                                             ,nam
                                             ,thang):

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
    gv_dilam_kehoachs = func_get_songay_dilam_giaovien_trongthang(giaovien2thang.giaovien_id,coso_dilam_kehoachs)

    gv_nghiles = func_get_giaovien_nghiles(giaovien,nghiles)
    gv_coso_chonghi_truluongs = func_get_giaovien_coso_nghi_truluong(giaovien, coso_chonghi_truluongs)


    duoc_chamcong = len(dilam_cangay)  + (len(dilam_nuabuoi) * 0.5)

    data ={
        'dilam_muon':len(dilam_muon),
        'dilam_nuabuoi':len(dilam_nuabuoi),
        'dilam_nghi':len(chamcong_nghi),
        'dilam_chamcong':duoc_chamcong,
        'gv_dilam_kehoach':gv_dilam_kehoachs,
        'gv_nghiles': gv_nghiles,
        'gv_coso_chonghi_truluongs': gv_coso_chonghi_truluongs

    }

    return data

def func_get_songay_dilam_giaovien_trongthang(giaovien,coso_dilam_kehoachs):
    ngay = 0
    if coso_dilam_kehoachs:
        for key in coso_dilam_kehoachs:
            day = coso_dilam_kehoachs.get(key)
            if day:
                is_dilam = func_is_dilam_trong_ngay(giaovien,day)
                if is_dilam == True:
                    ngay = ngay +1

    return ngay

def func_get_giaovien_nghiles(giaovien,nghiles):
    if giaovien.is_ngaydilam_rieng == False:
        return nghiles
    else:
        days={}
        for key in nghiles:
            day = string_util.string2date(key)
            is_dilam = func_is_dilam_trong_ngay(giaovien,day)
            if is_dilam == True:
                days[key] = nghiles.get(key)
        return days

def func_get_giaovien_coso_nghi_truluong(giaovien,coso_chonghi_truluongs):
    if giaovien.is_ngaydilam_rieng == False:
        return coso_chonghi_truluongs
    else:
        days={}
        for key in coso_chonghi_truluongs:
            day = string_util.string2date(key)
            is_dilam = func_is_dilam_trong_ngay(giaovien,day)
            if is_dilam == True:
                days[key] = coso_chonghi_truluongs.get(key)
        return days


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
    # 1. Chặn lỗi nếu chưa nhập ngày bắt đầu đi làm
    if not giaovien.dilam_tungay:
        return 0.0

    today = date.today()

    # 2. Xác định mốc thời gian chốt sổ (end_date)
    if giaovien.trangthai == "0":
        # Nếu đã nghỉ làm -> Tính đến ngày nghỉ việc.
        # (Giả định anh đang dùng trường 'ngay_nghiviec', hãy sửa lại tên biến nếu anh đặt tên khác)
        # Nếu quên chưa nhập ngày nghỉ, tạm lấy ngày hôm nay để tránh lỗi hệ thống
        end_date = giaovien.dilam_denngay if giaovien.dilam_denngay else today
    else:
        # Nếu trạng thái "1" (Đang làm việc) hoặc "2" (Nghỉ thai sản, ốm đau) -> Tính đến hôm nay
        end_date = today

    # 3. Chốt chặn an toàn: Tránh trường hợp nhập sai (ngày nghỉ trước ngày đi làm) gây ra số âm
    if end_date < giaovien.dilam_tungay:
        return 0.0

    # 4. Tính toán khoảng thời gian
    diff = relativedelta(end_date, giaovien.dilam_tungay)

    # Công thức: số năm + (số tháng / 12)
    result = diff.years + (diff.months / 12.0)

    return round(result, 1)



def func_danhsach_giaovien_khoang_thoigian(self, coso_ids, tu_ngay,den_ngay):
    domain =func_get_domain_trong_khoang_thoigian(coso_ids,tu_ngay,den_ngay)

    giaoviens = self.env['ekids.giaovien'].search(domain)

    return giaoviens

def func_danhsach_giaovien_trongthang(self, coso_id, nam, thang):
    days = ngay_util.func_get_cacngay_trong_thang(int(nam), int(thang))
    tu_ngay = days[0]
    den_ngay = days[len(days) - 1]
    coso_ids =[coso_id]
    domain =func_get_domain_trong_khoang_thoigian(coso_ids,tu_ngay,den_ngay)

    giaoviens = self.env['ekids.giaovien'].search(domain)

    return giaoviens





def func_get_domain_trong_khoang_thoigian(coso_ids, tu_ngay,den_ngay):


    domain_chung= [
        ('coso_id', 'in', coso_ids),
        ('dilam_tungay', '<=', den_ngay),
    ]

    # Nhóm 1: giáo viên đang làm việc
    domain_theohoc = [
        ('trangthai', '=', '1'),
    ]

    # Nhóm 2: giáo viên đã nghỉ việc nhưng vẫn được tính lương trong tháng, hoc giáo viên =2: Nghi thai sản
    domain_danghi = [
        ('trangthai', 'in', ['0','2']),
        ('dilam_denngay', '!=', False),
        ('dilam_denngay', '>=', tu_ngay),
        ('dilam_denngay', '<=', den_ngay),
    ]

    domain = expression.AND([
        domain_chung,
        expression.OR([
            domain_theohoc,
            domain_danghi
        ])
    ])

    return domain


from odoo import fields


def func_is_dilam_trong_ngay(giaovien, ngay):
    # 1. Ép biến 'ngay' về chuẩn Date duy nhất của Odoo ngay lập tức
    ngay_chuan = fields.Date.to_date(ngay)

    # Đề phòng trường hợp đầu vào rỗng hoặc lỗi
    if not ngay_chuan:
        return False

    # 2. Xử lý hàm weekday() an toàn trên biến đã chuẩn hóa
    week = ngay_chuan.weekday() + 2
    field_name = "hd_t" + str(week)

    # 3. Lấy và ép kiểu các mốc thời gian của giáo viên
    dilam_tungay = fields.Date.to_date(giaovien.dilam_tungay)
    dilam_denngay = fields.Date.to_date(giaovien.dilam_denngay)

    # 4. Kiểm tra điều kiện "Từ ngày" (chỉ kiểm tra nếu có dữ liệu)
    if dilam_tungay and ngay_chuan < dilam_tungay:
        return False

    # 5. Kiểm tra điều kiện "Đến ngày" (chỉ kiểm tra nếu có dữ liệu)
    if dilam_denngay and ngay_chuan > dilam_denngay:
        return False

    # 6. Kiểm tra lịch làm việc (Riêng hoặc theo Cơ sở)
    # Lược bỏ == True cho code gọn và chạy nhanh hơn theo chuẩn Python (PEP8)
    if giaovien.is_ngaydilam_rieng:
        is_dilam = getattr(giaovien, field_name)
        if is_dilam:
            return True
    else:
        coso = giaovien.coso_id
        is_dilam = getattr(coso, field_name)
        if is_dilam:
            return True

    return False




