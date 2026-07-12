from datetime import datetime, timedelta,date
from odoo.exceptions import UserError, ValidationError
from . import  ngay_util
# phần học phí khá phức tạp cần chekc xme có locked không
import json
from odoo.exceptions import UserError

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
def func_is_dl_diemdanh_locked(self,coso,nam,thang):
    is_locked = func_is_dl_locked(self,1,coso,nam,thang)
    if is_locked == True:
        raise UserError("Dữ liệu đã hết hiệu lực được sửa. Nếu thật sự cần sửa vui lòng liên hệ Quản trị phần mềm !.")
def func_is_dl_kpi_locked(self,coso,nam,thang):
    is_locked = func_is_dl_locked(self,2,coso,nam,thang)
    if self.env.is_admin():
        return False
    if is_locked == True:
        raise UserError("Dữ liệu đã hết hiệu lực được sửa. Nếu thật sự cần sửa vui lòng liên hệ Quản trị phần mềm !.")

def func_is_dl_locked(self,type,coso,nam,thang):
    if self.env.is_admin():
        return False
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

def func_is_dl_luong_locked(self,coso,trangthai):
    if self.env.is_admin():
        return False

    if not coso.trangthai_luong_khoa_dl:
        return False

    if trangthai in coso.trangthai_luong_khoa_dl.split(","):
        return  False
    else:
        return True




def func_is_dl_hocphi_locked(self,coso,trangthai):
    if self.env.is_admin():
        return False
    # 1. Nếu chuỗi JSON rỗng (chưa cấu hình), mặc định cho phép sửa (hoặc tùy logic của anh)

    json_string = coso.trangthai_hocphi_khoa_dl
    if not json_string:
        return False

    # 2. Cố gắng dịch (parse) chuỗi JSON thành Dictionary (Từ điển) của Python
    try:
        config_data = json.loads(json_string)
    except json.JSONDecodeError:
        raise UserError("Quản trị phần mềm đã cấu hình cho phép khóa dữ liệu Học phí nhưng lỗi, bạn vui lòng liên hệ quản trị để hỗ trợ !")

    # 3. Chuyển trạng thái về dạng chuỗi (string) để đảm bảo khớp với key trong JSON (VD: số 0 thành "0")
    trangthai_str = str(trangthai)

    # 4. Tra cứu xem trạng thái đó có nằm trong khai báo JSON không
    if trangthai_str in config_data:
        # Lấy giá trị của key 'edit', nếu không thấy thì mặc định là False để an toàn
        edit= config_data[trangthai_str].get('edit', True)
        if edit == False:
            return True
    else:
        # Trạng thái lạ không có trong JSON -> Khóa lại cho an toàn
        return True


def func_is_chuyen_trangthai(self,coso,tt_hientai,tt_dich):
    if self.env.is_admin():
        return True
    # 1. Nếu không có cấu hình, mặc định cho phép mọi dịch chuyển (hoặc tùy anh chặn lại)
    json_string = coso.trangthai_hocphi_khoa_dl
    if not json_string:
        return True

    try:
        config_data = json.loads(json_string)
    except Exception:
        raise UserError("Quản trị phần mềm đã cấu hình cho phép khóa dữ liệu Học phí nhưng lỗi, bạn vui lòng liên hệ quản trị để hỗ trợ !")



    # 2. Nếu trạng thái hiện tại không có trong cấu hình JSON
    if tt_hientai not in config_data:
        # Tùy nghiệp vụ: có thể cho qua hoặc chặn lại. Ở đây tôi chọn cho qua nếu chưa định nghĩa.
        return True

    # 3. Lấy danh sách các trạng thái được phép đi tiếp
    allowed_next_states = config_data[tt_hientai].get('trangthai_tieptheo', [])

    # 4. Kiểm tra trạng thái đích có nằm trong danh sách cho phép không
    if tt_dich in allowed_next_states:
        return True
    else:
        raise UserError("Học phí ở trạng thái này không cho phép [Chuyển] sang [Trạng thái] bạn vừa lựa chọn. vui lòng lựa chọn lại ! ")
        return False

def func_cauhinh_canthiep(self,coso,thamso,default):
    return func_cauhinh(self, coso, "KEHOACH_CANTHIEP", thamso, default)

def func_cauhinh_luong(self,coso,thamso,default):
    return func_cauhinh(self,coso,"LUONG",thamso,default)

def func_cauhinh(self,coso,loai,thamso,default):
    json_string = coso.cauhinh
    if not json_string:
        return None

    try:
        config_data = json.loads(json_string)
    except Exception:
        if default:
            return default
        else:
            raise UserError("Quản trị phần mềm Chưa cấu hình cho phần can thiệp của Cơ sở["+coso.name+"] vui lòng liên hệ ! ")



    # 2. Nếu trạng thái hiện tại không có trong cấu hình JSON
    if loai not in config_data:
        # Tùy nghiệp vụ: có thể cho qua hoặc chặn lại. Ở đây tôi chọn cho qua nếu chưa định nghĩa.
        if default:
            return default
        else:
            raise UserError(
                "Không thây tham số "+loai+ "của cơ sở[" + coso.name + "] vui lòng liên hệ quản trị phần mềm ! ")
    else:
        result = config_data[loai].get(thamso,[])
        if result:
            return result
        else:
            return default


