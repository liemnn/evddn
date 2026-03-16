from odoo import models, fields, api, _
from datetime import datetime, timedelta
from datetime import date
from odoo.exceptions import UserError


from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class ChamCongGiaoVien2ThangAbstractModel(models.AbstractModel):
    _name = 'ekids.chamcong_giaovien2thang_abstractmodel'
    _description = 'Các hàm phục vụ điểm danh'
    _abstract = True


    def action_mo_popup_chamcong_giaovien2thang_ngay(self, record_id=None, field_name=None, field_value='1'):
        if record_id and field_name and field_value:
            if self:
                thang =self.chamcong_loai2thang_id.thang
                nam =self.chamcong_loai2thang_id.nam
                ngay = field_name.lstrip("d")
                day = date(int(nam),int(thang),int(ngay))
                giaovien2thang =  self.env['ekids.chamcong_giaovien2thang'].browse(record_id)
                if giaovien2thang:
                    if field_value == "2" or field_value=='3':
                        #TH1: Nghỉ lễ
                        # TH3: học sinh nghỉ phép... tính là nghỉ học
                        self.func_tao_macdinh_diemdanh_ca2ngay_theo_ngay(giaovien2thang.giaovien_id.id,day)
                        return self.func_mo_popup_nghiles(self.coso_id.id,giaovien2thang,day)
                    elif field_value == "4":
                        #TH3: học sinh nghỉ phép
                        self.func_tao_macdinh_diemdanh_ca2ngay_theo_ngay(giaovien2thang.giaovien_id.id, day)
                        return self.func_mo_popup_nghiphep(self.giaovien_id.id,day)
                    else:
                        return self.func_mo_popup_chamcong_giaovien2ngay(self.giaovien_id.id, day,field_value)
    def func_mo_popup_chamcong_giaovien2ngay(self, giaovien_id, ngay,trangthai):
        giaovien2ngay = self.func_tao_chamcong_giaovien2ngay(giaovien_id, ngay,trangthai)
        if giaovien2ngay:
            self.func_tao_macdinh_diemdanh_ca2ngay_theo_ngay(giaovien_id,ngay)
            # Tạo default các ca can thiệp theo ngày
            view_form_id = self.env.ref("ekids_diemdanh.chamcong_giaovien2ngay_form").id
            return {
                "type": "ir.actions.act_window",
                "name": "Điểm danh ngày",
                "res_model": "ekids.chamcong_giaovien2ngay",
                "view_id": view_form_id,
                "view_mode": "form",
                "views": [(view_form_id, "form")],
                "res_id": giaovien2ngay.id,
                "target": "new",
                "context":{
                    "default_record_id":self.id,
                    'is_giaovien_tao':True
                }
            }

    def func_tao_chamcong_giaovien2ngay(self, giaovien_id, ngay, trangthai):
        giaovien2ngay = self.env['ekids.chamcong_giaovien2ngay'].search([
            ('giaovien_id', '=', giaovien_id),
            ('ngay', '=', ngay)

        ], limit=1)
        if not giaovien2ngay:
            if trangthai=='11':
                trangthai="1"
            data = {
                'giaovien_id': giaovien_id,
                'ngay': ngay,
                'trangthai': str(trangthai)
            }
            giaovien2ngay = self.env['ekids.chamcong_giaovien2ngay'].create(data)
        return giaovien2ngay





    def func_mo_popup_nghiphep(self,giaovien_id,ngay):
        nghiphep = self.env['ekids.giaovien_nghiphep'].search([
            ('giaovien_id', '=', giaovien_id),
            ('tu_ngay', '<=', ngay),
            ('den_ngay', '>=', ngay),
        ],limit=1)
        if nghiphep:
            view_form_id = self.env.ref("ekids_diemdanh.giaovien_nghiphep_form_inherit").id
            return {
                "type": "ir.actions.act_window",
                "name": "NGHỈ PHÉP",
                "res_model": "ekids.giaovien_nghiphep",
                "view_mode": "form",
                "views": [(view_form_id, "form")],
                "res_id": nghiphep.id,
                "target": "new",
                "context":{
                    'default_giaovien_id': giaovien_id,
                    'default_ngay': ngay,
                }
            }
    def func_mo_popup_nghiles(self,coso_id,giaovien2thang,ngay):
        nghile = self.env['ekids.nghile'].search([
            ('coso_id', '=', coso_id),
            ('tu_ngay', '<=', ngay),
            ('den_ngay', '>=', ngay),
        ],limit=1)
        if nghile:

            view_form_id = self.env.ref("ekids_diemdanh.nghile_form_inherit_view").id
            return {
                "type": "ir.actions.act_window",
                "name": "NGHỈ LẾ/NHÀ TRƯỜNG CHO NGHỈ",
                "res_model": "ekids.nghile",
                "view_mode": "form",
                "views": [(view_form_id, "form")],
                "res_id": nghile.id,
                "target": "new",
                "context":{
                    'default_giaovien_id': giaovien2thang.giaovien_id.id,
                    'default_ngay': ngay,
                }
            }
    def func_tinhtoan_hocbu_cho_hocsinh2thang_khoitao(self,diemdanh_thangtruoc):
        if diemdanh_thangtruoc:
            hocsinh2thangs = diemdanh_thangtruoc.hocsinh2thang_ids
            if hocsinh2thangs:
                for hocsinh2thang in hocsinh2thangs:
                    if (self.hocsinh_id.id == hocsinh2thang.hocsinh_id.id):
                        self.hocbu_thangtruoc = hocsinh2thang.hocbu_conlai


    def func_tao_macdinh_diemdanh_ca2ngay_theo_ngay(self,giaovien_id,ngay):

        weekday = ngay.weekday() + 2
        thu_field = 't' + str(weekday)
        ca_canthieps = self.env['ekids.hocsinh_ca_canthiep'].search([
                            ('giaovien_id', '=', giaovien_id)
                            ])
        if ca_canthieps:
            for ca_canthiep in ca_canthieps:
                is_canthiep = getattr(ca_canthiep,thu_field)
                if is_canthiep:
                    count = self.env['ekids.diemdanh_ca2ngay'].search_count([
                        ('giaovien_id', '=', giaovien_id),
                        ('ngay', '=', ngay),
                        ('hocphi_dm_ca_id', '=', ca_canthiep.dm_ca_id.id),

                    ])
                    if count <= 0:
                        data={

                            'hocphi_dm_ca_id': ca_canthiep.dm_ca_id.id,
                            'ngay': ngay,
                            'tu':ca_canthiep.tu,
                            'den': ca_canthiep.den,
                            'giaovien_id': giaovien_id,
                            'hocsinh_id': ca_canthiep.hocsinh_id.id,
                            'trangthai': '0',

                        }
                        self.env['ekids.diemdanh_ca2ngay'].create(data)









