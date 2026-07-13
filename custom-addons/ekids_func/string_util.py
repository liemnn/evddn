from datetime import datetime,date
import unicodedata
def number2string(total):
    total = "{:,.0f}".format(total)
    return total


def string2number(s):
    if not s:
        return 0
    # bỏ dấu phẩy ngăn cách hàng nghìn
    s = s.replace(",", "").strip()
    return float(s)


def date2string(date):
    return date2string_format(date,"%d/%m/%Y")

def date2string_format(date,format):
    if date:
        return date.strftime(format)
    else:
        return ""
def string2date(datestr):
    if datestr:
        return datetime.strptime(datestr,"%Y-%m-%d")
    else:
        return False

def xoa_tiengviet_codau(s):
    # Loại bỏ dấu tiếng Việt
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.replace('đ', 'd').replace('Đ', 'D')
