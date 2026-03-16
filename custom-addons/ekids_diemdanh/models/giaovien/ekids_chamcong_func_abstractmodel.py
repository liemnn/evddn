from odoo import models, fields, api, _
from datetime import datetime, timedelta
from datetime import date
from odoo.exceptions import UserError


from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class ChamCongFuncAbstractModel(models.AbstractModel):
    _name = 'ekids.chamcong_func_abstractmodel'
    _description = 'Các hàm phục vụ điểm danh'
    _abstract = True


    def func_tao_macdinh_chamcong_giaovien2thang(self):
        # b1: tìm tất cả học sinh học trong tháng này
        days = self.func_get_cacngay_trong_thang(int(self.nam), int(self.thang))
        ngay_cuoithang = days[len(days) - 1]
        giaoviens = self.env['ekids.giaovien'].search(
            [
                ('coso_id', '=', self.coso_id.id),
                ('trangthai', '=', '1'),
                ('dilam_tungay', '<=', ngay_cuoithang)
            ])
        if giaoviens:
            for gv in giaoviens:
                count = self.env['ekids.chamcong_giaovien2thang'].search_count(
                    [
                        ('coso_id', '=', self.coso_id.id),
                        ('chamcong_loai2thang_id', '=', self.id),
                        ('giaovien_id','=', gv.id)


                    ])
                if count<=0:
                    data = {
                        'chamcong_loai2thang_id': self.id,
                        'giaovien_id': gv.id,

                    }
                    self.env['ekids.chamcong_giaovien2thang'].create(data)
    def func_tao_macdinh_kpi_kpi2thang(self):
        # b1: tìm tất cả học sinh học trong tháng này
        days = self.func_get_cacngay_trong_thang(int(self.nam), int(self.thang))
        ngay_cuoithang = days[len(days) - 1]
        giaoviens = self.env['ekids.giaovien'].search(
            [
                ('coso_id', '=', self.coso_id.id),
                ('trangthai', '=', '1'),
                ('dilam_tungay', '<=', ngay_cuoithang)
            ])
        if giaoviens:
            for gv in giaoviens:
                count = self.env['ekids.chamcong_kpi2thang'].search_count(
                    [
                        ('chamcong_loai2thang_id', '=', self.id),
                        ('giaovien_id','=', gv.id)


                    ])
                if count<=0:
                    data = {
                        'coso_id': self.coso_id.id,
                        'chamcong_loai2thang_id': self.id,
                        'giaovien_id': gv.id,

                    }
                    self.env['ekids.chamcong_kpi2thang'].create(data)


    # kiêm tra một ngay xem cơ sở đó có hoạt động không
    def func_is_ngay_trong_thang_hoatdong(self, ngay,thang,nam, coso):

        try:
            day = date(int(nam), int(thang), ngay)
            today =date.today()
            if day > today:
                return False
            weekday = day.weekday() +2
            thu_field = 'hd_t' + str(weekday)
            is_hoc = getattr(coso, thu_field)
            return is_hoc

        except ValueError:
            return False

    def func_is_ngay_nghiphep_giaovien(self, giaovien_id,ngay,thang,nam):
        day = date(int(nam), int(thang), int(ngay))
        nghiphep = self.env['ekids.giaovien_nghiphep'].search_count([
                            ('giaovien_id','=',giaovien_id),
                            ('tu_ngay', '<=', day),
                            ('den_ngay', '>=', day),
                        ])
        if nghiphep > 0:
            return True
        else:
            return False

    def func_is_ngay_nghile_coso(self, coso, ngay, thang, nam):
        day = date(int(nam), int(thang), ngay)
        nghiphep = self.env['ekids.nghile'].search_count([
            ('coso_id', '=', coso.id),
            ('tu_ngay', '<=', day),
            ('den_ngay', '>=', day),
        ])
        if nghiphep > 0:
            return True
        else:
            return False











