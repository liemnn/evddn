from datetime import datetime, timedelta,date
from odoo import models, fields, api
import qrcode
import base64
import io

from . import  coso_util,ngay_util,string_util
from odoo.osv import expression

import logging
_logger = logging.getLogger(__name__)


def func_get_dihoc_diemdanh(self,hocsinh,ngay):

    nam =ngay.year
    thang = ngay.month
    hocsinh2thang = self.env['ekids.diemdanh_hocsinh2thang'].search([
        ('hocsinh_id', '=', hocsinh.id),
        ('diemdanh_id.thang', '=', str(thang)),
        ('diemdanh_id.nam', '=', str(nam))
    ],limit=1)
    if hocsinh2thang:
        field_name = "d" + str(ngay.day)
        giatri = getattr(hocsinh2thang, field_name, '-1')
        return giatri
    else:
        return "1"
    return None


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

def func_is_dangky_hoc(hocsinh,ngay):
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
        ('ngay_nghihoc', '!=', False),
        ('ngay_nghihoc', '>=', tu_ngay)
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




def func_tao_macdinh_diemdanh_ca2ngay_theo_ngay(self,hocsinh,ngay):
    # Ép toàn bộ biến về chuẩn Date an toàn bằng hàm lõi của Odoo
    d_ngay = fields.Date.to_date(ngay)
    d_nhaphoc = fields.Date.to_date(hocsinh.ngay_nhaphoc)
    d_nghihoc = fields.Date.to_date(hocsinh.ngay_nghihoc)

    # 1. Chặn lỗi ngầm nếu thiếu dữ liệu đầu vào
    if not d_ngay or not d_nhaphoc:
        return

    # 2. Xử lý logic: Nếu ngày đang xét trước ngày nhập học -> Bỏ qua
    if d_ngay < d_nhaphoc:
        return

    # 3. Xử lý logic: Nếu đã nghỉ học và ngày đang xét sau ngày nghỉ học -> Bỏ qua
    if d_nghihoc and d_ngay > d_nghihoc:
        return

    weekday = ngay.weekday() + 2
    thu_field = 't' + str(weekday)
    ca_canthieps = self.env['ekids.hocsinh_ca_canthiep'].search([
                        ('hocsinh_id', '=', hocsinh.id)
                        ])
    if ca_canthieps:
        for ca_canthiep in ca_canthieps:
            is_canthiep = getattr(ca_canthiep,thu_field)
            if is_canthiep:
                count = self.env['ekids.diemdanh_ca2ngay'].search_count([
                    ('hocsinh_id', '=', hocsinh.id),
                    ('ngay', '=', ngay),
                    ('hocsinh_ca_canthiep_id', '=', ca_canthiep.id),

                ])
                if count <= 0:
                    data={
                        'hocphi_dm_ca_id': ca_canthiep.dm_ca_id.id,
                        'hocsinh_ca_canthiep_id': ca_canthiep.id,
                        'ngay': ngay,
                        'tu':ca_canthiep.tu,
                        'den': ca_canthiep.den,
                        'hocsinh_id': hocsinh.id,
                        'trangthai': '0',

                    }
                    if ca_canthiep.giaovien_id:
                        data['giaovien_id'] = ca_canthiep.giaovien_id.id


                    self.env['ekids.diemdanh_ca2ngay'].create(data)


def func_tao_macdinh_diemdanh_ca2ngay_theo_ngay_nghiphep(self,hocsinh,ngay):
    # Ép toàn bộ biến về chuẩn Date an toàn bằng hàm lõi của Odoo
    d_ngay = fields.Date.to_date(ngay)
    d_nhaphoc = fields.Date.to_date(hocsinh.ngay_nhaphoc)
    d_nghihoc = fields.Date.to_date(hocsinh.ngay_nghihoc)

    # 1. Chặn lỗi ngầm nếu thiếu dữ liệu đầu vào
    if not d_ngay or not d_nhaphoc:
        return

    # 2. Xử lý logic: Nếu ngày đang xét trước ngày nhập học -> Bỏ qua
    if d_ngay < d_nhaphoc:
        return

    # 3. Xử lý logic: Nếu đã nghỉ học và ngày đang xét sau ngày nghỉ học -> Bỏ qua
    if d_nghihoc and d_ngay > d_nghihoc:
        return

    weekday = ngay.weekday() + 2
    thu_field = 't' + str(weekday)
    ca_canthieps = self.env['ekids.hocsinh_ca_canthiep'].search([
                        ('hocsinh_id', '=', hocsinh.id)
                        ])
    if ca_canthieps:
        for ca_canthiep in ca_canthieps:
            is_canthiep = getattr(ca_canthiep,thu_field)
            if is_canthiep:
                ca2ngay = self.env['ekids.diemdanh_ca2ngay'].search([
                    ('hocsinh_id', '=', hocsinh.id),
                    ('ngay', '=', ngay),
                    ('hocsinh_ca_canthiep_id', '=', ca_canthiep.id),

                ],limit=1)
                trangthai = "0" # se hoc bu
                if (ca_canthiep.dm_ca_id.is_hoantien_khi_nghi == True
                        or ca_canthiep.dm_ca_id.tyle_hoan_rieng > 0):
                    trangthai = "3"

                if not ca2ngay:
                    data={
                        'hocphi_dm_ca_id': ca_canthiep.dm_ca_id.id,
                        'hocsinh_ca_canthiep_id': ca_canthiep.id,
                        'ngay': ngay,
                        'tu':ca_canthiep.tu,
                        'den': ca_canthiep.den,
                        'hocsinh_id': hocsinh.id,
                        'trangthai': trangthai,

                    }
                    if ca_canthiep.giaovien_id:
                        data['giaovien_id'] = ca_canthiep.giaovien_id.id


                    self.env['ekids.diemdanh_ca2ngay'].create(data)
                else:
                    setattr(ca2ngay,"trangthai",trangthai)


def func_capnhat_macdinh_diemdanh_ca2ngay_theo_ngay_nghiphep(self,hocsinh,ngay):
    ca2ngays = self.env['ekids.diemdanh_ca2ngay'].search([
        ('hocsinh_id', '=', hocsinh.id),
        ('ngay', '=', ngay),

    ])
    if ca2ngays:
        for ca2ngay in ca2ngays:
            if ca2ngay.trangthai =="3":
                setattr(ca2ngay,"trangthai","0")


@staticmethod
def func_crc16_vietqr(data: str):
    """Thuật toán CRC16/CCITT-FALSE chuẩn Napas."""
    crc = 0xFFFF
    poly = 0x1021
    for char in data:
        crc ^= (ord(char) << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
        crc &= 0xFFFF
    return "{:04X}".format(crc)

def func_build_qr_code(hp):
    try:

        coso = hp.coso_id
        if (coso.bank_bin
            and coso.bank_acc_number):
            amount = str(int(round(float(hp.hocphi_phaidong))))  # Bỏ .00, làm tròn số
            bin_code = "".join(filter(str.isdigit, str(coso.bank_bin or "")))
            acc = "".join(filter(str.isdigit, str(coso.bank_acc_number or "")))

            # [Tag 38] - Phân cấp chuẩn Napas
            guid = "A000000727"
            service = "QRIBFTTA"

            # Lớp 01: Chứa BIN và ACC
            consumer = f"00{len(bin_code):02d}{bin_code}01{len(acc):02d}{acc}"

            # Lớp 38: Chứa GUID, CONSUMER và SERVICE
            merchant_info = (
                f"00{len(guid):02d}{guid}"
                f"01{len(consumer):02d}{consumer}"
                f"02{len(service):02d}{service}"
            )
            tag_38 = f"38{len(merchant_info):02d}{merchant_info}"

            # Các thông tin bổ sung (Tag 59, 60 - Bắt buộc cho Zalo)
            merchant_name = "EVDDN"  # Viết hoa không dấu
            merchant_city = "HANOI"
            tag_59 = f"59{len(merchant_name):02d}{merchant_name}"
            tag_60 = f"60{len(merchant_city):02d}{merchant_city}"


            # 1. Chuẩn bị nội dung (Tối đa 25 ký tự để tránh lỗi độ dài)
            # Ví dụ: "NGUYENVANA HP 06/2026"
            ten_hs = string_util.xoa_tiengviet_codau(hp.hocsinh_id.name or "HOC SINH").upper()
            thang = string_util.xoa_tiengviet_codau(hp.thang_id.name or "").upper()
            nam = string_util.xoa_tiengviet_codau(hp.nam_id.name or "").upper()

            # 2. Kết hợp nội dung: "TRAN VIET THANG HP THANG 06 2026"
            # Sử dụng f-string để ghép nối, giữ nguyên đầy đủ, giới hạn 25 ký tự an toàn
            noi_dung = f"{ten_hs} HP {thang} {nam}".strip()

            # 3. Xây dựng Tag 62
            sub_tag_08 = f"08{len(noi_dung):02d}{noi_dung}"
            tag_62 = f"62{len(sub_tag_08):02d}{sub_tag_08}"

            # 3. Ghép vào Payload (Đặt Tag 62 trước Tag 63)
            data = (
                    "000201"
                    "010212"
                    + tag_38 +
                    "5303704"
                    + f"54{len(amount):02d}{amount}"
                    + "5802VN"
                    + tag_59
                    + tag_60
                    + tag_62  # <--- THÊM VÀO ĐÂY
                    + "6304"
            )



            # Tính CRC
            payload = data + func_crc16_vietqr(data)

            #_logger.info("PAYLOAD_READY: %s", payload)  # Log để anh check

            # Tạo ảnh QR
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
            qr.add_data(payload)
            qr.make(fit=True)


            buffer = io.BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue())
        else:
            return False
    except Exception as e:
        _logger.error("Lỗi sinh QR với định dạng số tiền .00: %s", e)
        return False


def sum_tong_hocsinh_trong_thang(self, coso_ids,nam, thang):
    days = ngay_util.func_get_cacngay_trong_thang(nam, thang)
    if not days:
        return 0
    tu_ngay = days[0]  # Ngày đầu tiên của tháng
    den_ngay = days[-1]  # Ngày cuối cùng của tháng
    return sum_tong_hocsinh_trong_khoang_thoigian(self, coso_ids,tu_ngay,den_ngay)

def sum_tong_hocsinh_trong_khoang_thoigian(self, coso_ids,tu_ngay,den_ngay):


    # 1. Điều kiện cơ bản bắt buộc (Cơ sở, học phí và bắt buộc phải có ngày nhập học hợp lệ)
    domain = [
        ('coso_id', 'in', coso_ids),
        ('hocsinh_id.ngay_nhaphoc', '!=', False),
        ('hocsinh_id.ngay_nhaphoc', '<=', den_ngay)
    ]

    # 2. Định nghĩa 2 trạng thái bằng expression.OR
    # Trạng thái A: Học sinh hiện tại vẫn đang học (Chưa có ngày nghỉ)
    domain_danghoc = [('hocsinh_id.ngay_nghihoc', '=', False)]

    # Trạng thái B: Học sinh đã nghỉ nhưng ngày nghỉ nằm trong tháng này (tu_ngay -> den_ngay)
    domain_nghi_trongthang = [
        ('hocsinh_id.ngay_nghihoc', '!=', False),
        ('hocsinh_id.ngay_nghihoc', '>=', tu_ngay)

    ]

    # Gộp 2 trạng thái: Đang học HOẶC mới nghỉ trong tháng
    domain_hoc = expression.OR([
        domain_danghoc,
        domain_nghi_trongthang
    ])

    # 3. Kết hợp điều kiện cơ bản AND với trạng thái hợp lệ
    domain = expression.AND([domain, domain_hoc])

    # Tiến hành gom nhóm và đếm dữ liệu theo từng học sinh duy nhất
    result = self.env['ekids.hocphi'].read_group(
        domain=domain,
        fields=['hocsinh_id'],
        groupby=['hocsinh_id']
    )
    return len(result)

def sum_tong_hocsinh_nghi_trong_thang(self,coso_ids, nam, thang):
    # 1. Khởi tạo ngày đầu tháng hiện tại
    ngay_dau_thang = date(int(nam), int(thang), 1)

    # 2. Giảm đi 1 ngày để lấy ngày cuối cùng của tháng trước
    thangtruoc = ngay_dau_thang - timedelta(days=1)

    days = ngay_util.func_get_cacngay_trong_thang(thangtruoc.year, thangtruoc.month)
    if not days:
        return 0
    tu_ngay = days[0]  # Ngày đầu tiên của tháng
    den_ngay = days[-1]  # Ngày cuối cùng của tháng

    # 1. Điều kiện cơ bản bắt buộc (Cơ sở, học phí và bắt buộc phải có ngày nhập học hợp lệ)
    domain = [
        ('coso_id', 'in', coso_ids),
        ('hocsinh_id.ngay_nghihoc', '!=', False),
        ('hocsinh_id.ngay_nghihoc', '>=', tu_ngay),
        ('hocsinh_id.ngay_nghihoc', '<=', den_ngay)

    ]

    # Tiến hành gom nhóm và đếm dữ liệu theo từng học sinh duy nhất
    result = self.env['ekids.hocphi'].read_group(
        domain=domain,
        fields=['hocsinh_id'],
        groupby=['hocsinh_id']
    )
    return len(result)

def sum_tong_hocsinh_moi_trong_thang(self, coso_ids,nam, thang):
    days = ngay_util.func_get_cacngay_trong_thang(nam, thang)
    if not days:
        return 0
    tu_ngay = days[0]  # Ngày đầu tiên của tháng
    den_ngay = days[-1]  # Ngày cuối cùng của tháng

    # 1. Điều kiện cơ bản bắt buộc (Cơ sở, học phí và bắt buộc phải có ngày nhập học hợp lệ)
    domain = [
        ('coso_id', 'in', coso_ids),
        ('hocsinh_id.ngay_nhaphoc', '!=', False),
        ('hocsinh_id.ngay_nhaphoc', '>=', tu_ngay),
        ('hocsinh_id.ngay_nhaphoc', '<=', den_ngay)
    ]




    # Tiến hành gom nhóm và đếm dữ liệu theo từng học sinh duy nhất
    result = self.env['ekids.hocphi'].read_group(
        domain=domain,
        fields=['hocsinh_id'],
        groupby=['hocsinh_id']
    )
    return len(result)