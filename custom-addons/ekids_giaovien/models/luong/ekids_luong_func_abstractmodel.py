from odoo import models, fields, api, _
from datetime import datetime, timedelta
from datetime import date
from odoo.exceptions import UserError


from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import giaovien_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")


class LuongFuncAbstractModel(models.AbstractModel):
    _name = 'ekids.luong_func_abstractmodel'
    _description = 'Các hàm phục vụ luong'
    _abstract = True

    def action_view_khoitao_luong_giaovien(self):
        """action view year tuition"""
        self.ensure_one()
        days =ngay_util.func_get_cacngay_trong_thang(int(self.nam_id.name),int(self.name))
        ngay_dauthang =days[0]
        ngay_cuoithang = days[len(days)-1]
        coso = self.coso_id
        nam =ngay_dauthang.year
        thang= ngay_dauthang.month


        nghiles_all=nghile_util.func_get_nghiles_trong_khoang_thoigian(self,coso,None,ngay_dauthang,ngay_cuoithang)
        coso_nghiles = nghile_util.func_get_nghiles_trong_khoang_thoigian(self,coso,'0',ngay_dauthang,ngay_cuoithang)
        coso_chonghi_truluong = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, coso, '2', ngay_dauthang,
                                                                          ngay_cuoithang)
        coso_chonghis = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, coso, '1', ngay_dauthang,
                                                                          ngay_cuoithang)

        coso_dilam_kehoachs = giaovien_util.func_get_ngay_dilam_theo_kehoach(self,coso, nghiles_all,ngay_dauthang, ngay_cuoithang)
        #lay tat ca giao vien
        giaoviens= giaovien_util.func_get_giaoviens_trong_thang(self, coso.id, nam, thang)

        if giaoviens:
            for giaovien in giaoviens:
                ngay_dauthang_thucte = ngay_dauthang
                if giaovien.dilam_tungay > ngay_dauthang:
                    ngay_dauthang_thucte = giaovien.dilam_tungay
                nghipheps = (giaovien_util
                             .func_get_nghipheps_trong_khoang_thoigian(self,coso, giaovien, nghiles_all,'1', ngay_dauthang_thucte, ngay_cuoithang))
                # chỉ tính nghỉ phép bị trừ lương
                # xu ly lai di lam theo kế hoach phải tru ngay nghi phep ko tru luong di
                dl_chamcong = giaovien_util.func_get_dulieu_chamcong_thucte_giaovien(self,coso_dilam_kehoachs,giaovien,nghiles_all,nghipheps,nam,thang)
                self.func_tao_macdinh_luong_cho_giaovien(coso_nghiles,coso_chonghi_truluong,coso_chonghis,giaovien,nghiles_all,nghipheps,coso_dilam_kehoachs,dl_chamcong,ngay_dauthang_thucte,False)
            # B2 tinh toán khoảng lương su kiện
            self.func_tao_macdinh_luong_sukien(coso.id, ngay_dauthang.year, ngay_dauthang.month)

        name ='LƯƠNG THÁNG :' + self.name +"/" +self.nam_id.name
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'ekids.luong',
            'view_mode': 'list,kanban,form',
            'domain': [('thang_id', '=', self.id), ('coso_id', '=', self.coso_id.id)],
            'context': {

                'default_thang_id': self.id,
                'default_coso_id': self.coso_id.id,
                'default_nam': str(ngay_dauthang.year),
                'default_thang': str(ngay_dauthang.month)
            }



        }

    def func_tinhtoan_lai_luong_cho_mot_giaovien(self):
        """action view year tuition"""
        nam = int(self.nam_id.name)
        thang = int(self.thang_id.name)
        days =ngay_util.func_get_cacngay_trong_thang(nam,thang)
        ngay_dauthang =days[0]
        ngay_cuoithang = days[len(days)-1]
        coso = self.coso_id



        nghiles_all=nghile_util.func_get_nghiles_trong_khoang_thoigian(self,coso,None,ngay_dauthang,ngay_cuoithang)
        coso_nghiles = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, coso, '0', ngay_dauthang, ngay_cuoithang)
        coso_chonghi_truluong = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, coso, '2', ngay_dauthang,
                                                                                   ngay_cuoithang)
        coso_chonghis = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, coso, '1', ngay_dauthang, ngay_cuoithang)

        coso_dilam_kehoachs = giaovien_util.func_get_ngay_dilam_theo_kehoach(self,coso, nghiles_all,ngay_dauthang, ngay_cuoithang)
        #lay tat ca hoc sinh tung hoc trong thang xem.
        giaovien = self.giaovien_id
        ngay_dauthang_thucte = ngay_dauthang
        if giaovien.dilam_tungay > ngay_dauthang:
            ngay_dauthang_thucte = giaovien.dilam_tungay
        nghipheps= (giaovien_util
                     .func_get_nghipheps_trong_khoang_thoigian(self,coso, giaovien, nghiles_all,'1', ngay_dauthang_thucte, ngay_cuoithang))

        # chỉ tính nghỉ phép bị trừ lương
        # xu ly lai di lam theo kế hoach phải tru ngay nghi phep ko tru luong di
        dl_chamcong = giaovien_util.func_get_dulieu_chamcong_thucte_giaovien(self,coso_dilam_kehoachs,giaovien,nghiles_all,nghipheps,nam,thang)
        self.func_tao_macdinh_luong_cho_giaovien(coso_nghiles,coso_chonghi_truluong,coso_chonghis,giaovien,nghiles_all,nghipheps,coso_dilam_kehoachs,dl_chamcong,ngay_dauthang_thucte,True)
        # B2 tinh toán khoảng lương su kiện
        self.func_tao_macdinh_luong_sukien(coso.id, ngay_dauthang.year, ngay_dauthang.month)






    def func_tao_macdinh_luong_cho_giaovien(self,coso_nghiles,coso_chonghi_truluong,coso_chonghis,giaovien,nghiles,nghipheps,coso_dilam_kehoachs,dl_chamcong,ngay_dauthang,is_tinhlai):
        # B2:kiem tra xem giáo vin này đã có bang tinh lương chưa
        thang = ngay_dauthang.month
        nam =ngay_dauthang.year

        luong=None
        if is_tinhlai==True:
            luong = self.env['ekids.luong'].search(
                [('giaovien_id', '=', giaovien.id)
                    , ('thang_id', '=', self.thang_id.id)
                 ],limit=1)
        else:


            count = self.env['ekids.luong'].search_count(
                [('giaovien_id', '=', giaovien.id)
                    , ('thang_id', '=', self.id)
                 ])
            if count <= 0:
                data = {
                    'coso_id': self.coso_id.id,
                    'thang_id': self.id,
                    'giaovien_id': giaovien.id,
                    'trangthai': '-1' # trang thai đang tính lương
                }
                #B1: Công tác tính toán đảm bảo hiệu năng
                luong = self.env['ekids.luong'].create(data)

        #Tinh Luong
        if luong:
            #B3: Lấy ve toàn bộ cấu trúc lương của giáo viên
            cautruc_luongs =giaovien.dm_chitra_ids

            parameters = self.func_get_parameters(coso_nghiles,coso_chonghi_truluong,coso_chonghis,giaovien, luong, nghiles, nghipheps, coso_dilam_kehoachs, dl_chamcong,nam, thang)
            if cautruc_luongs:
                MAP = self.func_khoitao_map_cautruc_luong(cautruc_luongs)
                self.func_dequy_tinhluong(MAP,giaovien,luong,nam,thang,parameters)

    def func_get_parameters(self,coso_nghiles,coso_chonghi_truluong,coso_chonghis,giaovien,luong,nghiles,nghipheps,coso_dilam_kehoachs,dl_chamcong,nam,thang):
        parameters = {}
        parameters['nghiles'] = nghiles
        parameters['nghipheps'] = nghipheps
        parameters['dilam_kehoachs'] = coso_dilam_kehoachs

        parameters["$NGAY_CONG_QUYDINH"] = str(len(coso_dilam_kehoachs))
        luong.so_ngaycong_quydinh = len(coso_dilam_kehoachs)

        giaovien2thang = giaovien_util.func_get_chamcong_giaovien2thang(self,giaovien, nam,thang)
        parameters['duoc_chamcongs'] = giaovien2thang


        duoc_chamcongs_dimuon = dl_chamcong['dilam_muon']
        duoc_chamcong_nghi = dl_chamcong['dilam_nghi']
        duoc_chamcongs_nuabuoi= dl_chamcong['dilam_nuabuoi']
        duoc_chamcong = dl_chamcong['dilam_chamcong']


        parameters["$NGAY_DILAM"] = str(duoc_chamcong)

        chamcong_nghi = duoc_chamcong_nghi + (duoc_chamcongs_nuabuoi * 0.5) + len(coso_chonghi_truluong)

        parameters["$NGAY_NGHI"] = str(chamcong_nghi)
        #luong.so_ngaynghi = chamcong_nghi

        ngay_cong_tinhluong =len(coso_dilam_kehoachs) -chamcong_nghi
        parameters["$NGAY_CONG_TINH_LUONG"] = str(ngay_cong_tinhluong)
        luong.so_ngaycong = ngay_cong_tinhluong

        # xu ly ngay nghi le nghi phep
        parameters["$NGHILE"] = str(len(coso_nghiles))
        parameters["$NHATRUONG_NGHI"] = str(len(coso_chonghis))
        parameters["$NGHIPHEP"] = str(len(nghipheps))

        tong_ngaynghi =chamcong_nghi + len(coso_nghiles) +len(coso_chonghis)+len(nghipheps)
        parameters["$TONG_NGAYNGHI"] = str(tong_ngaynghi)
        luong.so_ngaynghi = tong_ngaynghi


        chamcong_muon = duoc_chamcongs_dimuon
        parameters["$NGAY_DIMUON"] = str(chamcong_muon)

        tham_nien = giaovien_util.func_get_thamnien(giaovien)
        parameters["$THAM_NIEN"] = str(tham_nien)
        luong.tham_nien = tham_nien

        hs_in_thang = hocsinh_util.func_get_so_hocsinh_trong_thang(self, giaovien.coso_id.id, nam, thang)
        parameters["$TONG_HS_TRONG_THANG"] = str(hs_in_thang)


        return parameters



    def func_tao_macdinh_luong_sukien(self,coso_id,nam,thang):
        luong_sukiens = self.env["ekids.luong_sukien"].search([
            ('coso_id', '=', coso_id),
            ('nam', '=', nam),
            ('thang', '=', thang)

        ])
        if luong_sukiens:
            for luong_sukien in  luong_sukiens:
                giaovien_ids = luong_sukien.giaovien_ids
                if giaovien_ids:
                    for giaovien_id in giaovien_ids:
                        luong_sukien.func_tao_luong_sukien_cho_giaovien(giaovien_id,nam,thang)












    def func_get_ngay_duoc_chamcong_giaoviec_trong_khoang_thoigian(self,giaovien, nghiles, nghipheps,
                                                               dilam_kehoachs,cautruc_luong):
        days = {}
        if dilam_kehoachs:
            key = list(dilam_kehoachs.keys())[0]  # Lấy key đầu tiên
            ngay = dilam_kehoachs[key]  # Lấy giá trị tương ứng

            month = ngay.month
            year = ngay.year
            chamcong = self.env['ekids.chamcong_giaovien2thang'].search([
                ('giaovien_id', '=', giaovien.id),
                ('chamcong_loai2thang_id.chamcong_loai_id.dm_chamcong_id', '=', cautruc_luong.dm_chamcong_id.id),
                ('chamcong_loai2thang_id.thang', '=', str(month)),
                ('chamcong_loai2thang_id.nam', '=', str(year)),
            ],limit=1)
            if chamcong:
                for key in dilam_kehoachs:
                    day = dilam_kehoachs.get(key)
                    dayofmonth = day.day
                    field_day = 'd' + str(dayofmonth)
                    is_chamcong = getattr(chamcong, field_day)
                    if is_chamcong == True:
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




    def func_get_danhsach_ngay_dilam_theo_kehoach(self, coso,nghiles,tu_ngay, den_ngay):

        ngay = tu_ngay
        days = {}
        while ngay <= den_ngay:
            is_coso_hoatdong = coso_util.func_is_coso_hoatdong(coso, ngay)
            if is_coso_hoatdong:
                # Co so hoat dong
                if nghiles:
                    is_nghile = nghiles.get(str(ngay), False)
                    if not is_nghile:
                        days[str(ngay)] = ngay
                else:
                    days[str(ngay)] = ngay

            ngay += timedelta(days=1)
        return days

















