from odoo import api, fields, models
from datetime import datetime,date, timedelta
import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
    from odoo.addons.ekids_func import hocsinh_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")



class HocPhiThangAbstractModel(models.AbstractModel):
    _name = 'ekids.hocphi_thang_abstractmodel'
    _description = 'Tạo lập trang thai group'
    _abstract = True

    def action_view_khoitao_hocphi_hocsinh(self):
        """action view year tuition"""
        self.ensure_one()
        today = date.today()
        year =today.year
        month =today.month

        days =ngay_util.func_get_cacngay_trong_thang(int(self.nam_id.name),int(self.name))
        ngay_dauthang =days[0]
        ngay_cuoithang = days[len(days)-1]
        coso = self.coso_id
        #lay tat ca hoc sinh tung hoc trong thang xem.
        nam =int(self.nam_id.name)
        thang =int(self.name)
        hocsinhs = hocsinh_util.func_get_hocsinhs_trong_thang(self,coso.id,nam,thang)

        if year != ngay_dauthang.year or month != ngay_dauthang.month:
            hocsinh_nghis = self.env['ekids.hocsinh'].search(
                [('coso_id', '=', self.coso_id.id)
                    , ('trangthai', '=', '3')
                    , ('ngay_nhaphoc', '<=', ngay_cuoithang)
                    , ('ngay_nghihoc', '>=', ngay_cuoithang)

                 ])
            hocsinhs =hocsinhs +hocsinh_nghis


        if hocsinhs:
            coso_nghiles = nghile_util.func_get_nghiles_trong_khoang_thoigian(self,coso, ['0','2'], ngay_dauthang, ngay_cuoithang)
            # tinh toan ngay cua thang truoc
            ngay = ngay_dauthang - timedelta(days=1)
            if coso.is_thu_hocphi_dauthang == False:
                #Thu học phí vào cuối tháng
                ngay =ngay_dauthang

            thangtruoc_days = ngay_util.func_get_cacngay_trong_thang(ngay.year, ngay.month)
            ngay_dauthang_truoc = thangtruoc_days[0]
            ngay_cuoithang_truoc = thangtruoc_days[len(thangtruoc_days) - 1]
            nghiles_thangtruoc = nghile_util.func_get_nghiles_trong_khoang_thoigian(self,coso, ['0','2'], ngay_dauthang_truoc, ngay_cuoithang_truoc)
            ngay_dihoc_cosos = (hocsinh_util
                                .func_get_ngay_dihoc_cua_coso(coso, coso_nghiles, ngay_dauthang, ngay_cuoithang))


            for hocsinh in hocsinhs:
                ngay_dauthang_thucte =ngay_dauthang
                if hocsinh.ngay_nhaphoc > ngay_dauthang:
                    ngay_dauthang_thucte= hocsinh.ngay_nhaphoc
                self.func_tao_macdinh_hocphi_cho_hocsinh(coso
                                                         ,coso_nghiles
                                                         ,nghiles_thangtruoc
                                                         ,ngay_dihoc_cosos
                                                          ,hocsinh
                                                         ,ngay_dauthang_thucte
                                                         ,ngay_cuoithang
                                                         ,thangtruoc_days
                                                         ,False
                                                         )
                # Tinh toán các khoản thu ngoài
            #B2tinh toán các khoảng thu ngoài
            self.func_tao_macdinh_hocphi_thungoai(coso.id, ngay_dauthang.year, ngay_dauthang.month)

        name ='HỌC PHÍ THÁNG:' + self.name+"/"+ self.nam_id.name
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'ekids.hocphi',
            'view_mode': 'list,kanban,form',
            'domain': [('thang_id', '=', self.id), ('coso_id', '=', self.coso_id.id)],
            'context': {
                'default_thang_id': self.id,
                'default_coso_id': self.coso_id.id,
                'default_thang': self.name,
                'default_nam': self.nam_id.name,
            }



        }



    def func_tao_macdinh_hocphi_cho_hocsinh(self
                                            ,coso
                                            ,nghiles
                                            ,nghiles_thangtruoc
                                            ,ngay_dihoc_cosos
                                            ,hocsinh
                                            ,ngay_dauthang
                                            ,ngay_cuoithang
                                            ,thangtruoc_days,is_tinhlai):
        hocphi =None
        thu_bantrus = hocsinh.thu_bantru_ids
        if is_tinhlai == True:
            #TH1: Áp dụng cho tính toán lại
            hocphi = self.env['ekids.hocphi'].search(
                [('coso_id', '=', self.coso_id.id)
                    , ('thang_id', '=', self.id)
                    , ('hocsinh_id', '=', hocsinh.id)
                 ],limit=1)

        else:
            #TH2: Khởi tạo hoặc tính toán lại toàn bộ
            # B2:kiem tra xem hocsinh này đã có bang tinh hoc phi chua
            count = self.env['ekids.hocphi'].search_count(
                [('coso_id', '=', self.coso_id.id)
                    , ('thang_id', '=', self.id)
                    , ('hocsinh_id', '=', hocsinh.id)
                 ])
            if count <= 0:
                data = {
                    'coso_id': self.coso_id.id,
                    'thang_id': self.id,
                    'hocsinh_id': hocsinh.id,
                    'tyle_giamhocphi':0,
                    'trangthai': '-1'
                }

                #B1: Công tác tính toán đảm bảo hiệu năng
                hocphi = self.env['ekids.hocphi'].create(data)
        if hocphi:
            ca_canthieps = self.func_get_danhmuc_ca_cua_hocsinh(hocsinh)
            ca2thus =self.func_get_dm_ca_hocsinh_ngay_trong_tuan(hocsinh,ca_canthieps)

            ngay_dihoc_kehoachs = (hocsinh_util
                                    .func_get_ngay_dihoc_kehoachs(coso,nghiles,hocsinh,ngay_dauthang,ngay_cuoithang))

            #B2: vào tính toán các phần
            hocphi.ngay_dihoc = len(ngay_dihoc_kehoachs)
            hocphi.ngay_dihoc_coso = len(ngay_dihoc_cosos)

            if ngay_dihoc_kehoachs:
                self.func_tao_macdinh_hocphi_bantru(hocphi,thu_bantrus, len(ngay_dihoc_kehoachs),len(ngay_dihoc_cosos))

                # Tinh toan khoang thu ca can thiệp
                self.func_tao_macdinh_hocphi_ca(hocphi,ca_canthieps,ca2thus,ngay_dihoc_kehoachs,ngay_dihoc_cosos)
                # tin hoc phi do giam hoc phi theo so tien cu the

                # tinh toan tháng trước để được trừ
                if thangtruoc_days:
                    ngay_dauthang = thangtruoc_days[0]
                    ngay_cuoithang = thangtruoc_days[len(thangtruoc_days) - 1]

                    if hocsinh.ngay_nhaphoc > ngay_dauthang:
                        ngay_dauthang = hocsinh.ngay_nhaphoc

                    self.func_tao_macdinh_hocphi_duoctru_thangtruoc(coso
                                                         ,nghiles_thangtruoc
                                                         ,hocphi
                                                         ,hocsinh
                                                         ,thu_bantrus
                                                         ,ngay_dauthang
                                                         ,ngay_cuoithang,ngay_dihoc_cosos)
            #B3: Tính chính sách giảm học phí cho học sinh
            if hocsinh.dm_chinhsach_giam_id:
                hocphi.tyle_giamhocphi = 0
                hocphi.tyle_giamhocphi_bantru = 0
                hocphi.tyle_giamhocphi_ca = 0
                if hocsinh.dm_chinhsach_giam_id.is_giam_theo_tyle == True:
                     # chỉ tính cho trường hợp chính sách giảm học phí theo tỷ lệ
                    hocphi.tyle_giamhocphi =hocsinh.dm_chinhsach_giam_id.tyle_giam
                    hocphi.tyle_giamhocphi_bantru = hocsinh.dm_chinhsach_giam_id.tyle_giam
                    hocphi.tyle_giamhocphi_ca = hocsinh.dm_chinhsach_giam_id.tyle_giam
                else:
                    self.func_tao_khoantru_giam_hocphi_sotien(hocsinh,hocphi)

                hocphi.dm_chinhsach_giam_id = hocsinh.dm_chinhsach_giam_id.id
                hocphi._compute_hocphi_giam()
                hocphi._compute_hocphi_phaidong()



                # tạo default số tiền lớp chung
                # self.create_default_hocphi_bantru(hs,hocphi,False)

    def func_tao_khoantru_giam_hocphi_sotien(self,hocsinh,hocphi):
       dm_giam = hocsinh.dm_chinhsach_giam_id
       if dm_giam and dm_giam.is_giam_theo_tyle == False:
            data = {
                'hocphi_id': hocphi.id,
                'name': dm_giam.name,
                'tien': dm_giam.tien
            }
            self.env['ekids.hocphi_duoctru'].create(data)


    def func_tinhtoan_lai_hocphi_cho_mot_hocsinh(self):
        thang = int(self.thang_id.name)
        nam = int(self.nam_id.name)
        #B1 xoa dữ liệu cũ
        bantrus = self.hocphi_bantru_ids
        if bantrus:
            for bantru in bantrus:
                bantru.unlink()
        cas = self.hocphi_ca_ids
        if cas:
            for ca in cas:
                ca.unlink()
        trus = self.hocphi_duoctru_ids
        if trus:
            for tru in trus:
                tru.unlink()
        #B2 tinh toán la học phí

        days = ngay_util.func_get_cacngay_trong_thang(nam,thang)
        ngay_dauthang = days[0]
        ngay_cuoithang = days[len(days) - 1]
        coso = self.coso_id
        # lay tat ca hoc sinh tung hoc trong thang xem.

        coso_nghiles = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, coso, ['0','2'], ngay_dauthang,
                                                                     ngay_cuoithang)
        # tinh toan ngay cua thang truoc
        ngay = ngay_dauthang - timedelta(days=1)
        if coso.is_thu_hocphi_dauthang == False:
            # Thu học phí vào cuối tháng
            ngay = ngay_dauthang
        thangtruoc_days = ngay_util.func_get_cacngay_trong_thang(ngay.year, ngay.month)
        ngay_dauthang_truoc = thangtruoc_days[0]
        ngay_cuoithang_truoc = thangtruoc_days[len(thangtruoc_days) - 1]
        nghiles_thangtruoc = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, coso, ['0','2'],

                                                                                        ngay_dauthang_truoc,
                                                                                        ngay_cuoithang_truoc)

        hocsinh =self.hocsinh_id
        hocphi_thang = self.thang_id
        ngay_dihoc_cosos = (hocsinh_util
                            .func_get_ngay_dihoc_cua_coso(coso, coso_nghiles, ngay_dauthang, ngay_cuoithang))

        ngay_dauthang_thucte = ngay_dauthang
        if hocsinh.ngay_nhaphoc > ngay_dauthang:
            ngay_dauthang_thucte = hocsinh.ngay_nhaphoc
        hocphi_thang.func_tao_macdinh_hocphi_cho_hocsinh(coso
                                                     , coso_nghiles
                                                     , nghiles_thangtruoc
                                                     ,ngay_dihoc_cosos
                                                     , hocsinh
                                                     , ngay_dauthang
                                                     , ngay_cuoithang
                                                     , thangtruoc_days
                                                     , True)


    # function get default giá trị của tháng trước cho tháng tạo lập học phí, bán trú
    # nêu đặt  is get defaul =true có nghĩa lấy giá trị tháng trước
    def func_tao_macdinh_hocphi_bantru(self,hocphi,thu_bantrus,songay_dihoc_quydinh,songay_dihoc_coso):
        if thu_bantrus:
            for thu_bantru in thu_bantrus:
                tien = thu_bantru.tien
                desc = ""
                if thu_bantru.loai == '0':
                    #TH1: Thu cố định theo tháng
                    tien = thu_bantru.tien
                    desc = ""
                elif thu_bantru.loai == '1':
                    # TH2: Khoản thu = so tien * Ngày đi học thực tế
                    tien = (songay_dihoc_quydinh * thu_bantru.tien)
                    tienstr = string_util.number2string(thu_bantru.tien)
                    desc = str(songay_dihoc_quydinh) + ' ngày đi học x ' + tienstr + " vnđ/buổi"

                elif thu_bantru.loai == '2':
                    # TH3: Khoản thu = (Số tiền/Ngày đi học của tháng) * Ngày đi học thực tế
                    if songay_dihoc_coso >0:
                        tien = (thu_bantru.tien /songay_dihoc_coso) * songay_dihoc_quydinh
                    else:
                        tien = thu_bantru.tien

                    desc = "(đi học "+str(songay_dihoc_quydinh)+"/" + str(songay_dihoc_coso)+" ngày)"
                else:
                    # TH4 là công thức
                    tien = thu_bantru.tien

                namestr =thu_bantru.name
                if desc:
                    namestr =namestr+ " "+desc
                data = {
                    'hocphi_id': hocphi.id,
                    'name': namestr,
                    'dm_thu_bantru_id':thu_bantru.id,
                    'tien': tien

                }
                self.env['ekids.hocphi_bantru'].create(data)

    def func_tao_macdinh_hocphi_thungoai(self,coso_id,nam,thang):
        thungoais = self.env["ekids.hocphi_thungoai"].search([
            ('coso_id', '=', coso_id),
            ('nam', '=', nam),
            ('thang', '=', thang)

        ])
        #B1: xóa toàn bộ thu ngoài cho học phí tháng này
        if thungoais:
            for thungoai in thungoais:
                hocphi_bantrus = self.env["ekids.hocphi_bantru"].search([
                    ('hocphi_id.coso_id', '=', coso_id),
                    ('hocphi_id.thang_id.name', '=', thang),
                    ('hocphi_id.nam_id.name', '=', nam),
                    ('thungoai_id', '=', thungoai.id)

                ])
                if hocphi_bantrus:
                    for hocphi_bantru in hocphi_bantrus:
                        hocphi_bantru.unlink()

        #B2: tạo lập dữ liệu thu ngoài cho học phí mới

        if thungoais:
            for thungoai in  thungoais:
                hocsinh_ids = thungoai.hocsinh_ids
                if hocsinh_ids:
                    for hocsinh_id in hocsinh_ids:
                        thungoai.func_tao_hocphi_thungoai_cho_hocsinh(hocsinh_id,nam,thang)

    def func_get_sotien_hocphi_bantru_duoctru(self,hocphi,thu_bantrus
                                              ,so_ngaynghi
                                              ,so_ngay_dihoc_theoquydinh):
        tien =0
        if thu_bantrus:
            for thu_bantru in thu_bantrus:
                if thu_bantru.is_hoantien_khi_nghi == True:
                    # xác định hoàn trả học phí
                    if thu_bantru.loai == '0':
                        # TH1: Cố định nên không được trừ
                       continue
                    elif thu_bantru.loai == '1':
                        # TH2: Khoản trừ = Số tiền  * Ngày đi học thực tế
                        tien = tien +  (so_ngaynghi * thu_bantru.tien)

                    else:
                        # TH3: Khoản thu = (Số tiền/Ngày đi học của tháng) * Ngày đi học thực tế
                        sotientheongay = (thu_bantru.tien / so_ngay_dihoc_theoquydinh)
                        tien = tien + (sotientheongay * so_ngaynghi)

        tien = self.func_thongtin_duoctru_hocphi_tien(tien,hocphi)
        return  tien

    def func_tao_macdinh_hocphi_ca(self,hocphi,ca_canthieps,ca2thus,ngay_dihoc_kehoachs,ngay_dihoc_cosos):
        if ca_canthieps:
            for dm_ca in ca_canthieps:
               soca = self.func_get_tong_soca_macdinh_trong_khoang_thoigian(ca2thus,dm_ca.id,ngay_dihoc_kehoachs)
               if soca > 0:
                   tien =soca * dm_ca.tien
                   # tien thu tron goi theo thang
                   if dm_ca.is_tien_trongoi == True:
                       tien = soca * (dm_ca.tien/len(ngay_dihoc_cosos))
                   data = {
                        'hocphi_id': hocphi.id,
                        'dm_ca_id':dm_ca.id,
                        'soca':soca,
                        'tien':tien,
                        'desc': dm_ca.desc,

                    }
                   self.env['ekids.hocphi_ca'].create(data)



    # Đây là hàm tính toán số ngày hoc trong tháng của hoc sinh
    # 1. lay ra so ngay trong thang
    # tru di ngay co so không hoat dong
    # tinh toan so ngay nghi le va lam bu
    def func_get_tong_soca_macdinh_trong_khoang_thoigian(self,ca2thus,dm_ca_id,ngay_dihoc_theoquydinh):
        total=0
        if ngay_dihoc_theoquydinh:
            for day in ngay_dihoc_theoquydinh:
                ngay = ngay_dihoc_theoquydinh.get(day)
                weekday = ngay.weekday() + 2
                key = str(dm_ca_id)+"_t"+str(weekday)
                ca2thu = ca2thus.get(key)
                if ca2thu:
                    # TH2.1:  co thiet lap ca trong thu nay
                    total = total + ca2thu.soca

        # tra ve ket qua
        return total


    def func_get_ngay_diemdanh_nghi_trong_khoang_thoigian(self,hocsinh,nghiles,nghipheps,ngay_dihoc_kehoachs):
        days={}
        if ngay_dihoc_kehoachs:
            key = list(ngay_dihoc_kehoachs.keys())[0]  # Lấy key đầu tiên
            ngay = ngay_dihoc_kehoachs[key]  # Lấy giá trị tương ứng

            month =ngay.month
            year = ngay.year
            diemdanh =  self.env['ekids.diemdanh_hocsinh2thang'].search([
                            ('hocsinh_id','=',hocsinh.id),
                            ('diemdanh_id.thang', '=', month),
                            ('diemdanh_id.nam', '=', year),
                            ])
            if diemdanh:
                for key in ngay_dihoc_kehoachs:
                    day = ngay_dihoc_kehoachs.get(key)
                    dayofmonth =day.day
                    field_day ='d'+str(dayofmonth)
                    giatri = getattr(diemdanh,field_day)
                    if (giatri == '-1' or giatri =='0'):
                        # Học sinh nghỉ hoặc đi học nửa buổi
                        nghile = nghiles.get(key)
                        nghiphep = nghipheps.get(key)
                        if (nghile or nghiphep):
                            continue
                        else:
                            days[key] = day
        return days







     # tinh toan ca nghi tru tien thang truoc
    def func_tao_macdinh_hocphi_duoctru_thangtruoc(self
                                        ,coso
                                        ,nghiles
                                        ,hocphi
                                        ,hocsinh
                                        ,thu_bantrus
                                        ,ngay_dauthang
                                        ,ngay_cuoithang
                                        ,ngay_dihoc_cosos):

        dihoc_kehoachs = (hocsinh_util
                          .func_get_ngay_dihoc_kehoachs(coso, nghiles,hocsinh,ngay_dauthang, ngay_cuoithang))


        #TH1: Tính học phí được trừ: Nhà trường cho nghi
        nhatruong_nghis = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, coso, ['1'], ngay_dauthang, ngay_cuoithang)
        self.func_tao_hocphi_duoctru_thangtruoc_do_loai('Nhà trường nghỉ ',hocphi
                                                    ,coso.tyle_tralai_coso_chonghi
                                                    ,thu_bantrus
                                                    ,nhatruong_nghis,dihoc_kehoachs,ngay_dihoc_cosos)
        # TH2: học sinh xin nghỉ phép
        nghipheps =(hocsinh_util
                    .func_get_nghipheps_trong_khoang_thoigian(self,coso
                                                                          ,hocsinh
                                                                          ,nghiles
                                                                          ,nhatruong_nghis
                                                                          ,ngay_dauthang
                                                                          ,ngay_cuoithang))

        self.func_tao_hocphi_duoctru_thangtruoc_do_hocsinh_nghiphep(hocphi
                                                                    , coso.tyle_tralai_hs_nghiphep
                                                                    , thu_bantrus
                                                                    , nghipheps
                                                                    ,dihoc_kehoachs
                                                                    ,ngay_dihoc_cosos)


        #TH3: Nghỉ đột suất, điểm danh nghỉ
        diemdanh_nghis= self.func_get_ngay_diemdanh_nghi_trong_khoang_thoigian(hocsinh
                                                                                               ,nghiles
                                                                                               ,nghipheps
                                                                                               ,dihoc_kehoachs)
        self.func_tao_hocphi_duoctru_thangtruoc_do_loai('Vắng ', hocphi
                                                        , coso.tyle_tralai_hs_vangmat
                                                        ,thu_bantrus
                                                        , diemdanh_nghis
                                                        , dihoc_kehoachs
                                                        ,ngay_dihoc_cosos)

        # Bổ sung tiền ca tăng cường tháng trước
        self.func_tao_hocphi_ca_tangcuong_thangtruoc(hocphi,ngay_dauthang,ngay_cuoithang)

    def func_tao_hocphi_ca_tangcuong_thangtruoc(self,hocphi,tu_ngay,den_ngay):
        ca2ngays= self.env['ekids.diemdanh_ca2ngay'].search([
            ('hocsinh_id', '=', hocphi.hocsinh_id.id),
            ('ngay', '>=', tu_ngay),
            ('ngay', '<=', den_ngay),
            ('trangthai', '=','5')
        ])
        # các ca tăng cường
        if ca2ngays:
            tien =0
            for ca2ngay in ca2ngays:
                tien = tien+ ca2ngay.hocphi_dm_ca_id.tien
            if tien >0:

                namestr = "Học tăng cường tháng trước("+ str(len(ca2ngays))+" ca)"
                data = {
                    'hocphi_id': hocphi.id,
                    'name': namestr,
                    'tien': tien

                }
                self.env['ekids.hocphi_bantru'].create(data)

    def func_tao_hocphi_duoctru_thangtruoc_do_hocsinh_nghiphep(self,hocphi,tyle_hoantra,thu_bantrus,nghipheps,ngay_dihoc_kehoachs,ngay_dihoc_cosos):
        if nghipheps:
            tien =0
            #TH1 tính toán bán trú

            name = "Nghỉ có phép "+str(len(nghipheps)) +" ngày"
            name = self.func_thongtin_duoctru_hocphi_name(name, hocphi)

            #TH1: tính toán trừ các khoản bán trú
            tien = self.func_get_sotien_hocphi_bantru_duoctru(hocphi,thu_bantrus
                                                                     ,len(nghipheps)
                                                                     ,len(ngay_dihoc_kehoachs))
            if tien >0 :
                #tien= (tien / 100) * tyle_hoantra
                name = name + " Hoàn 100% tiền bán trú="+string_util.number2string(tien)+" vnđ;"




                #TH2 tính toán các ngày nghỉ phép chia 2 loại:
            nghiphep_thongles = {}
            nghiphep_riengs={}
            for key in nghipheps:
                nghiphep = nghipheps.get(key)
                if (nghiphep
                    and nghiphep.is_hoantra_hocphi == True
                    and int(nghiphep.tyle_hoantra_hocphi) != tyle_hoantra):
                    nghiphep_riengs[key] =nghipheps[key]
                elif nghiphep:
                    nghiphep_thongles[key] =nghipheps[key]

            if nghiphep_riengs and len(nghiphep_riengs)>0:
                #TH4: tính toán nghỉ phép riêng

                nghiphep_tinhtoans={}
                tyle_check=-1
                index =0
                for key in nghiphep_riengs:
                    nghiphep = nghiphep_riengs.get(key)
                    if int(nghiphep.tyle_hoantra_hocphi) != tyle_check:
                        if index > 0:
                            data=self.func_tinhtoan_lydo_tien_do_hocsinh_nghiphep(hocphi, tyle_check, nghiphep_tinhtoans,ngay_dihoc_cosos)

                            tien = tien + int(data['tien'])
                            name = name + data['name']
                            nghiphep_tinhtoans={}

                        tyle_check =int(nghiphep.tyle_hoantra_hocphi)
                        nghiphep_tinhtoans[key] = nghiphep

                        index = index +1
                    else:
                        nghiphep_tinhtoans[key] = nghiphep
                # lần cuối cùng
                data =self.func_tinhtoan_lydo_tien_do_hocsinh_nghiphep(hocphi, tyle_check, nghiphep_tinhtoans,ngay_dihoc_cosos)
                tien = tien + int(data['tien'])
                name = name + data['name']




            if nghiphep_thongles and len(nghiphep_thongles)>0:
                #TH4: tính toán nghỉ phép thông le
                days = list(nghiphep_thongles.keys())
                data =self.func_tinhtoan_lydo_tien_do_hocsinh_nghiphep(hocphi,tyle_hoantra,nghiphep_thongles,ngay_dihoc_cosos)
                tien = tien + int(data['tien'])
                name = name + data['name']

            if tien >0:
                data = {
                    'hocphi_id': hocphi.id,
                    'name': name,
                    'tien': tien
                }
                self.env['ekids.hocphi_duoctru'].create(data)

    def func_tinhtoan_lydo_tien_do_hocsinh_nghiphep(self,hocphi,tyle,nghipheps,ngay_dihoc_cosos):
        name = ""

        days = list(nghipheps.keys())
        # lấy cả các ca nghỉ, và sẽ dạy bù phục vụ thông báo
        data = self.func_tinhtoan_tien_ca_duoctru(hocphi, tyle, days,ngay_dihoc_cosos)
        tien = int(data['tien'])
        name = name +data['name']
        data['tien']= tien
        data['name'] = name
        return data





    def func_tao_hocphi_duoctru_thangtruoc_do_loai(self,lydo,hocphi,tyle_hoantra,thu_bantrus,ngaynghis,ngay_dihoc_kehoachs,ngay_dihoc_cosos):
            #TH1: nghỉ và thiết lập tỷ lệ hoàn trả

        if ngaynghis:
            tien = 0
            #TH2: nghỉ theo thông lệ
            name = lydo+ str(len(ngaynghis)) + " ngày"
            name = self.func_thongtin_duoctru_hocphi_name(name, hocphi)

            #TH1: tính toán trừ các khoản bán trú
            tien = self.func_get_sotien_hocphi_bantru_duoctru(hocphi,thu_bantrus
                                                                     ,len(ngaynghis)
                                                                     ,len(ngay_dihoc_kehoachs))

            if tien >0 :
               #tien_bantru = (tien / 100) * tyle_hoantra
                name = name + " Hoàn 100% bán trú "+string_util.number2string(tien)+" vnđ"
                #TH2: tính trừ các khoản can can thiệp
            # các ca: nghỉ, nghỉ hoa trả học phí đều được trừ: [-1: nghỉ, 2:Nghỉ và hoàn tra hoc phi]
            days = list(ngaynghis.keys())
            # lấy cả các ca nghỉ, và sẽ dạy bù phục vụ thông báo
            data = self.func_tinhtoan_tien_ca_duoctru(hocphi, tyle_hoantra, days,ngay_dihoc_cosos)
            tien_ca = int (data['tien'])
            name = name+data['name']
            tien =tien +tien_ca
            if tien > 0:
                data={
                    'hocphi_id': hocphi.id,
                    'name':name,
                    'tien':tien
                }
                self.env['ekids.hocphi_duoctru'].create(data)



    def func_tinhtoan_tien_ca_duoctru(self,hocphi,tyle_hoantra,days,ngay_dihoc_cosos):
        tien =0
        ca_nghi = 0
        ca_se_daybu = 0

        for day in days:
            ngay = datetime.strptime(day, "%Y-%m-%d").date()
            tinhtoan_ca2thus = hocsinh_util.func_get_tinhtoan_ca2thu_theo_thu(self, hocphi.hocsinh_id, ngay)
            if tinhtoan_ca2thus:
                for tinhtoan_ca2thu in tinhtoan_ca2thus:
                    if tinhtoan_ca2thu.dm_ca_id.is_hoantien_khi_nghi == True:
                        ca2ngays = self.env['ekids.diemdanh_ca2ngay'].search([
                            ('hocsinh_id', '=', hocphi.hocsinh_id.id),
                            ('hocphi_dm_ca_id', '=', tinhtoan_ca2thu.dm_ca_id.id),
                            ('ngay', '=', ngay),

                        ])
                        gia_ca = tinhtoan_ca2thu.dm_ca_id.tien
                        if tinhtoan_ca2thu.dm_ca_id.is_tien_trongoi == True:
                            #don gia tron goi
                            gia_ca = (tinhtoan_ca2thu.dm_ca_id.tien/ len(ngay_dihoc_cosos))

                        if not ca2ngays:
                            # TH1: không có chấm công ca này
                            ca_nghi = ca_nghi + int(tinhtoan_ca2thu.soca)
                            tien = tien + (gia_ca * tinhtoan_ca2thu.soca)
                        else:
                            for ca2ngay in ca2ngays:
                                trangthai = ca2ngay.trangthai
                                if trangthai in ['0', '-1', '2']:
                                    ca_nghi = ca_nghi + 1
                                    tien = tien + gia_ca
                                elif trangthai == '3':
                                    # nghi sẽ dạy bù
                                    ca_se_daybu = ca_se_daybu + 1
        name=""
        if tyle_hoantra <=0:
            tien =0
        if ca_nghi > 0 and tyle_hoantra>0:
            name = ". Hoàn " + str(tyle_hoantra) + "% trong đó:"
            tien = (tien / 100) * tyle_hoantra
            tien = self.func_thongtin_duoctru_hocphi_tien(tien,hocphi)
            name = name + "trừ tiền ca " + string_util.number2string(tien) + " vnđ(" + str(ca_nghi) + " ca);"
        if ca_se_daybu > 0:
            name = name + "; còn " + str(ca_se_daybu) + " ca sẽ được học bù trong tháng;"
        data = {}
        data['tien'] = tien
        data['name'] = name
        return data







    def func_get_danhmuc_ca_cua_hocsinh(self, hocsinh):
        domain = [('hocsinh_id', '=', hocsinh.id),
                  ('dm_ca_id.trangthai', '=', '1')
                  ]

        ca_canthieps = self.env['ekids.hocsinh_ca_canthiep'].search(domain)
        result = []
        if ca_canthieps:
            # B1: Gộp theo danh mục ca
            for ca_canthiep in ca_canthieps:
                # loai tru cac phan tu trung nhau
                if ca_canthiep.dm_ca_id in result:
                    continue
                else:
                    result.append(ca_canthiep.dm_ca_id)
        return result

    def func_get_dm_ca_hocsinh_ngay_trong_tuan(self, hocsinh,ca_canthieps):
        ca2thus = {}
        if (ca_canthieps and len(ca_canthieps) > 0):
            for ca in ca_canthieps:
                for thu in range(2, 9):
                    key = str(ca.id)+"_t"+str(thu)
                    ca2thu = self.env['ekids.tinhtoan_ca2thu'].search([
                        ('hocsinh_id', '=', hocsinh.id),
                        ('dm_ca_id', '=', ca.id),
                        ('dm_ca_id.trangthai', '=', '1'),
                        ('thu', '=', thu)
                    ])
                    if ca2thu:
                        ca2thus[key] =ca2thu


        return ca2thus





    def func_thongtin_duoctru_hocphi_name(self,name,hocphi):
        hocsinh =hocphi.hocsinh_id
        if hocsinh.dm_chinhsach_giam_id:
            tyle =hocsinh.dm_chinhsach_giam_id.tyle_giam
            if tyle >0:
                name = name+"(đã giảm "+str(tyle)+"%)"
        name = name+"→"
        return name

    def func_thongtin_duoctru_hocphi_tien(self,tien,hocphi):
        hocsinh =hocphi.hocsinh_id
        if hocsinh.dm_chinhsach_giam_id:
            tyle =hocsinh.dm_chinhsach_giam_id.tyle_giam
            if tyle >0:
                tien = (tien/100)* (100-tyle)
        return tien

