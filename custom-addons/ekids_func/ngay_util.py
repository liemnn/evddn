from datetime import datetime, timedelta,date
def func_get_cacngay_trong_thang(nam, thang):
    result = []
    for i in range(1, 32):
        try:
            day = date(nam, thang, i)
            result.append(day)
        except:
            continue
    return result

def func_is_thang_nay(ngay):
    today = date.today()
    if today.year == ngay.year:
        if today.month == ngay.month:
            return True
    return False
def func_is_blocked(nam,thang):
    today = date.today()
    if today.year == nam:
        if today.month == thang:
            return False
        if today.month-1 == thang:
            return False
    return True



def func_get_ngays_cho_tinh_hocphi(nam, thang):
    result= {}
    days = func_get_cacngay_trong_thang(int(nam), int(thang))
    ngay_dauthang = days[0]
    ngay_cuoithang = days[len(days) - 1]
    result["ngay_dauthang"] = ngay_dauthang
    result["ngay_cuoithang"] = ngay_cuoithang

    day = ngay_dauthang - timedelta(days=1)
    thangtruoc_days = func_get_cacngay_trong_thang(day.year, day.month)
    ngay_dauthang_truoc = thangtruoc_days[0]
    ngay_cuoithang_truoc = thangtruoc_days[len(thangtruoc_days) - 1]
    result["ngay_dauthang_truoc"] = ngay_dauthang_truoc
    result["ngay_cuoithang_truoc"] = ngay_cuoithang_truoc
    return result



def get_ngays_luive_mungmot(self):

    today = date.today()

    # today.day trả về số của ngày hôm nay (VD: 18)
    # range(18) sẽ tạo ra chuỗi 0, 1, 2, ..., 17
    # Lấy today trừ lùi đi i ngày sẽ ra được danh sách giảm dần từ 18 về 1
    days = [today - timedelta(days=i) for i in range(today.day)]

    return days




