from odoo import models, fields, api, _
from datetime import datetime, timedelta
from datetime import date
from odoo.exceptions import UserError

from odoo.exceptions import ValidationError


import logging
_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import giaovien_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
    from odoo.addons.ekids_func import formula_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")


class LuongFolmulaAbstractModel(models.AbstractModel):
    _name = 'ekids.luong_formula_abstractmodel'
    _description = 'Các hàm phục vụ luong'
    _abstract = True

    def func_khoitao_map_cautruc_luong(self,cautruc_luongs):
        MAP ={}
        for cautruc_luong in cautruc_luongs:
            key = cautruc_luong.code
            data = {
                'cautruc_luong':cautruc_luong,
                'tien':None,
            }
            MAP.setdefault(key,data)
            MAP.__setitem__(key,data)
        return MAP

    def func_dequy_tinhluong(self,MAP,giaovien,luong,nam,thang,parameters):
        is_finish =True
        for key, value in MAP.items():
            if value['tien'] == None:
                is_finish = False
                cautruc_luong = value['cautruc_luong']
                tien = self.func_tinhluong_theo_cautruc_luong(MAP,giaovien,luong,cautruc_luong,nam,thang,parameters)
                if tien != None:
                    value['tien'] =tien
                    MAP.__setitem__(key,value)
                else:
                    continue
            else:
                continue
        if is_finish == True:
            return MAP
        else:
            return self.func_dequy_tinhluong(MAP,giaovien,luong,nam,thang,parameters)



    def func_tinhluong_theo_cautruc_luong(self,MAP,giaovien,luong,cautruc_luong,nam,thang,parameters):
        tien=0
        if (cautruc_luong.luong_cocau == '0'
                or cautruc_luong.luong_cocau == '2'):
            # TH1: Lương là thông tin hoặc nhà trường chi trả
            loai =cautruc_luong.luong_cocau
            tien =self.func_tao_luong_theo_cautruc_luong_thongtin(MAP,giaovien,loai,luong,cautruc_luong,parameters)
        else:
            # TH2: Tinh toan cho ca khoang + va -
            loai = cautruc_luong.luong_cocau
            if cautruc_luong.luong_loai == "0":
                # TH2.1: Loai lương cố định áp dụng cho cả + và -
                tien =self.func_tao_luong_theo_cautruc_luong_codinh(MAP,giaovien,loai, luong, cautruc_luong,parameters)
            else:
                # TH2.2 Loại lương có điều kiện
                if cautruc_luong.dieukien_loai == '1':
                    # TH2.2.1: Giao KPI
                    tien =self.func_tao_luong_theo_cautruc_luong_dieukien_kpi(MAP,giaovien, loai, luong, cautruc_luong, thang,
                                                                        nam,parameters)


                elif cautruc_luong.dieukien_loai == '0':
                    # TH2.2.2: Giao Bản chấm công
                    tien =self.func_tao_luong_theo_cautruc_luong_dieukien_chamcong(MAP,giaovien,loai, luong,
                                                                             cautruc_luong,parameters)
                elif cautruc_luong.dieukien_loai == '2':
                    # TH3 Giao việc hoàn thanh
                    tien = self.func_tao_luong_theo_cautruc_luong_dieukien_giaoviec(MAP, giaovien, loai, luong,
                                                                                    cautruc_luong, parameters)
                else:
                    # TH3 Giao việc gia tri dieukien_loai=3
                    tien =self.func_tao_luong_theo_cautruc_luong_dieukien_giaoviec_giatri(MAP,giaovien, loai, luong,
                                                                             cautruc_luong,parameters)



        return tien

    def func_tao_luong_theo_cautruc_luong_thongtin(self,MAP,giaovien,loai,luong,cautruc_luong,parameters):
        tien = formula_util.formula_tinhtoan_sotien(MAP, giaovien, cautruc_luong, parameters)
        desc = formula_util.formula_get_desc(MAP, giaovien, cautruc_luong, parameters)

        if (tien != None and tien > 0):
            data = {
                'luong_id': luong.id,
                'name': cautruc_luong.name,
                'desc':desc,
                'tien': tien,
                'loai': loai
            }
            self.env['ekids.luong_hangmuc'].create(data)
            return tien
        elif (tien != None and tien == 0):
            return 0
        else:
            return None

    def func_tao_luong_theo_cautruc_luong_dieukien_giaoviec(self,MAP,giaovien,loai,luong,cautruc_luong,parameters):
            dilam_kehoachs = parameters['dilam_kehoachs']
            congviec2thang = self.func_get_chamcong_congviec2thang(giaovien, dilam_kehoachs, cautruc_luong)
            if congviec2thang:
                duoc_chamcong = congviec2thang.tong
                parameters["$KETQUA"] = str(duoc_chamcong)
                tien = formula_util.formula_tinhtoan_sotien(MAP, giaovien, cautruc_luong,parameters)
                name = cautruc_luong.name
                desc = str(duoc_chamcong) +" "+ cautruc_luong.dm_chamcong_id.donvi

                if (tien != None and tien>0):
                    data = {
                        'luong_id': luong.id,
                        'name': name,
                        'tien': tien,
                        'desc':desc,
                        'loai': loai
                    }
                    self.env['ekids.luong_hangmuc'].create(data)
                    return tien
                elif (tien != None and tien==0):
                    return 0
                else:
                    return None
            else:
                return 0




    def func_get_chamcong_congviec2thang(self,giaovien,dilam_kehoachs,cautruc_luong):
        if dilam_kehoachs:
            key = list(dilam_kehoachs.keys())[0]  # Lấy key đầu tiên
            ngay = dilam_kehoachs[key]  # Lấy giá trị tương ứng

            month = ngay.month
            year = ngay.year
            chamcong = self.env['ekids.chamcong_congviec2thang'].search([
                ('giaovien_id', '=', giaovien.id),
                ('chamcong_loai2thang_id.chamcong_loai_id.dm_chamcong_id', '=', cautruc_luong.dm_chamcong_id.id),
                ('chamcong_loai2thang_id.thang', '=', str(month)),
                ('chamcong_loai2thang_id.nam', '=', str(year)),
            ],limit=1)
            return chamcong


    def func_tao_luong_theo_cautruc_luong_dieukien_giaoviec_giatri(self,MAP,giaovien,loai,luong,cautruc_luong,parameters):
            dilam_kehoachs = parameters['dilam_kehoachs']
            congviec2thang = self.func_get_chamcong_congviec2thang_giatri(giaovien, dilam_kehoachs, cautruc_luong)
            if congviec2thang:
                duoc_chamcong = congviec2thang.tong
                parameters["$KETQUA"] = str(duoc_chamcong)
                tien = formula_util.formula_tinhtoan_sotien(MAP, giaovien, cautruc_luong,parameters)
                name = cautruc_luong.name
                desc = str(duoc_chamcong) +" "+ cautruc_luong.dm_chamcong_id.donvi

                if (tien != None and tien>0):
                    data = {
                        'luong_id': luong.id,
                        'name': name,
                        'tien': tien,
                        'desc':desc,
                        'loai': loai
                    }
                    self.env['ekids.luong_hangmuc'].create(data)
                    return tien
                elif (tien != None and tien==0):
                    return 0
                else:
                    return None
            else:
                return 0

    def func_get_chamcong_congviec2thang_giatri(self,giaovien,dilam_kehoachs,cautruc_luong):
        if dilam_kehoachs:
            key = list(dilam_kehoachs.keys())[0]  # Lấy key đầu tiên
            ngay = dilam_kehoachs[key]  # Lấy giá trị tương ứng

            month = ngay.month
            year = ngay.year
            chamcong = self.env['ekids.chamcong_congviec2thang_giatri'].search([
                ('giaovien_id', '=', giaovien.id),
                ('chamcong_loai2thang_id.chamcong_loai_id.dm_chamcong_id', '=', cautruc_luong.dm_chamcong_id.id),
                ('chamcong_loai2thang_id.thang', '=', str(month)),
                ('chamcong_loai2thang_id.nam', '=', str(year)),
            ],limit=1)
            return chamcong


    def func_tao_luong_theo_cautruc_luong_dieukien_chamcong(self,MAP,giaovien,loai,luong,cautruc_luong,parameters):
        tien = formula_util.formula_tinhtoan_sotien(MAP, giaovien, cautruc_luong,parameters)
        desc = self.func_get_desc_theo_cautruc_luong_dieukien_chamcong(MAP,giaovien,cautruc_luong,parameters)

        if (tien != None and tien > 0):
            name = cautruc_luong.name
            data = {
                'luong_id': luong.id,
                'name': name,
                'tien': tien,
                'desc':desc,
                'loai': loai
            }
            self.env['ekids.luong_hangmuc'].create(data)
            return tien
        elif (tien !=None and tien ==0):
            return 0
        else:
            return None

    def func_get_desc_theo_cautruc_luong_dieukien_chamcong(self,MAP,giaovien,cautruc_luong,parameters):
        formule =cautruc_luong.formula
        desc =cautruc_luong.desc
        if (not desc or desc.strip()==""):
            desc=""
            if formule:
                if "$THAM_NIEN" in formule:
                    thamnien = parameters.get("$THAM_NIEN")
                    desc = desc+"Thâm niên="+str(thamnien)+" năm\n"

                if "$NGAY_DILAM" in formule:
                    dilam_quydinh = parameters.get("$NGAY_CONG_QUYDINH")
                    dilam_chamcong = parameters.get("$NGAY_DILAM")
                    dilam_nghi = parameters.get("$NGAY_NGHI")
                    if float(dilam_nghi) > 0.0:
                       desc = desc + "Nghỉ " + str(dilam_nghi) + " ngày trong tháng\n"
        else:
            desc = formula_util.formula_get_desc(MAP, giaovien, cautruc_luong, parameters)


        return desc






    def func_tao_luong_theo_cautruc_luong_dieukien_kpi(self,MAP,giaovien,loai,luong,cautruc_luong,thang, nam,parameters):
        tien=0
        name= cautruc_luong.name
        desc =""


        dm_chamcong_id =cautruc_luong.dm_chamcong_id.id
        formula_text = cautruc_luong.formula
        domain =[('giaovien_id', '=', giaovien.id),
                 ('chamcong_loai2thang_id.chamcong_loai_id.dm_chamcong_id', '=',dm_chamcong_id),
                 ('chamcong_loai2thang_id.thang', '=', str(thang)),
                 ('chamcong_loai2thang_id.nam', '=', str(nam))
                 ]
        kpi = self.env['ekids.chamcong_kpi2thang'].search(domain)
        if kpi:
            kpi2thang_ketquas = kpi.kpi2thang_ketqua_ids
            if kpi2thang_ketquas:
                for kq in kpi2thang_ketquas:
                    parameters["$"+kq.code] = str(kq.tong)
                    if "$"+kq.code in formula_text:
                        desc = desc +kq.name+"=" + str(kq.tong) + " "+str(kq.donvi)+".\n"


                tien = formula_util.formula_tinhtoan_sotien(MAP,giaovien,cautruc_luong,parameters)


        # TẠO BẢN GHI
        if tien != None and tien >0:
            data = {
                'luong_id': luong.id,
                'name': name,
                'desc':desc,
                'tien': tien,
                'loai': loai
            }
            self.env['ekids.luong_hangmuc'].create(data)
            return tien
        elif tien != None and tien ==0:
            return 0
        else:
            return None

    def func_tao_luong_theo_cautruc_luong_codinh(self, MAP,giaovien,loai, luong, cautruc_luong,parameters):
        tien = formula_util.formula_tinhtoan_sotien(MAP, giaovien, cautruc_luong, parameters)
        desc = self.func_get_desc_theo_cautruc_luong_dieukien_chamcong(MAP,giaovien,cautruc_luong,parameters)
        if (tien != None and tien >0):
            data = {
                'luong_id': luong.id,
                'name': cautruc_luong.name,
                'tien': tien,
                'desc':desc,
                'loai': loai
            }
            self.env['ekids.luong_hangmuc'].create(data)
            return tien
        elif (tien != None and tien == 0):
            return 0
        else:
            return None
