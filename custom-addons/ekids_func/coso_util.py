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

