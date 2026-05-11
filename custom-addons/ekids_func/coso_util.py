from datetime import datetime, timedelta,date
from odoo.exceptions import UserError, ValidationError
from . import  ngay_util

def func_is_coso_hoatdong(coso,ngay):
    weekday = ngay.weekday() + 2
    thu_field = 'hd_t' + str(weekday)
    is_hoc = getattr(coso, thu_field)
    return is_hoc

def func_get_ngay_hoatdongs(coso,nam,thang):

    try:
        days = ngay_util.func_get_cacngay_trong_thang(nam, thang)
        result = {}
        for day in days:
            today =date.today()

            weekday = day.weekday() +2
            thu_field = 'hd_t' + str(weekday)
            is_hoc = getattr(coso, thu_field)
            if is_hoc:
                result[str(day)]=True
            else:
                result[str(day)] = False
        return result
    except ValueError:
        return None


def func_check_errors(nam,thang):
    today =date.today()
    if  today.year == nam and today.month == thang:
        return True
    else:
        return True
        #raise UserError("Không thể thực hiện hành động này. Tháng thực hiện đã được khóa")

#type một số như sau: 0: dl chitieu,1: dữ liệu điểm danh
def func_is_dl_diemdanh_locked(coso,nam,thang):
    is_locked = func_is_dl_locked(1,coso,nam,thang)
    if is_locked == True:
        raise UserError("Dữ liệu đã hết hiệu lực được sửa. Nếu thật sự cần sửa vui lòng liên hệ Quản trị phần mềm !.")
def func_is_dl_kpi_locked(coso,nam,thang):
    is_locked = func_is_dl_locked(2,coso,nam,thang)
    if is_locked == True:
        raise UserError("Dữ liệu đã hết hiệu lực được sửa. Nếu thật sự cần sửa vui lòng liên hệ Quản trị phần mềm !.")

def func_is_dl_locked(type,coso,nam,thang):
    #type=1 : diem danh; type=2: Kpi phải lui một tháng
    if type in [1,2]:
        if int(coso.sothang_khoa_dl_diemdanh) <=0 :
            # không thiết lập
            return False
    today = date.today()
    thang_n = (today.year *12) + today.month
    thang_m = (nam*12)+thang
    if type in [2]:
        # kpi cần lùi 1 tháng
        thang_n =thang_n-1

    if (thang_n -thang_m) >= int (coso.sothang_khoa_dl_diemdanh):
        return True
    else:
        return False

def func_is_dl_luong_locked(coso,trangthai):
    if not coso.trangthai_luong_khoa_dl:
        return False

    if trangthai in coso.trangthai_luong_khoa_dl.split(","):
        return  False
    else:
        return True
