from datetime import datetime,date
import unicodedata
import re
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


def _is_html_empty(html_content):
    if not html_content:
        return True
    # Cạo sạch toàn bộ thẻ HTML đóng mở dạng <p>, <br>, <div>...
    clean_text = re.sub(r'<[^>]*>', '', html_content)
    # Khử tiếp thực thể khoảng trắng đặc biệt &nbsp; và strip() khoảng trống
    clean_text = clean_text.replace('&nbsp;', '').strip()
    return len(clean_text) == 0


# 🌟 Hàm helper dùng chung để kiểm tra field Char có trống hoặc toàn dấu cách không
def _is_char_empty(char_content):
    if not char_content:
        return True
    return len(char_content.strip()) == 0
