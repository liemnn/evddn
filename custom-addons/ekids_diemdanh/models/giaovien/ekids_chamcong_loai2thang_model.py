from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError
import calendar
from .ekids_chamcong_func_abstractmodel import  ChamCongFuncAbstractModel

import logging
_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import giaovien_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")



class ChamCongLoai2Thang(models.Model,ChamCongFuncAbstractModel):
    _name = "ekids.chamcong_loai2thang"
    _description = "Điểm danh học sinh theo học"

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True,ondelete ="restrict")
    chamcong_loai_id = fields.Many2one("ekids.chamcong_loai", string="Loại chấm công", required=True,ondelete ="cascade")
    name = fields.Char(string="Tên hiển thị", compute="_compute_name", readonly=True)
    thang = fields.Selection(
        [('1', 'Tháng 1'),('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'),
         ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'),
         ('11', 'Tháng 11'), ('12', 'Tháng 12')],
        string='Tháng',required=True,
         default = lambda self: str(date.today().month))
    nam = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year - 10, datetime.now().year + 1)]
        , string="Năm",required=True, default=lambda self: str(date.today().year))


    kpi2thang_ids = fields.One2many("ekids.chamcong_kpi2thang",
                                        "chamcong_loai2thang_id", string="Thuộc Tháng chấm công")

    giaovien2thang_ids = fields.One2many("ekids.chamcong_giaovien2thang",
                                    "chamcong_loai2thang_id", string="Thuộc Tháng chấm công")

    congviec2thang_ids = fields.One2many("ekids.chamcong_congviec2thang",
                                         "chamcong_loai2thang_id", string="Thuộc Tháng chấm công")

    @api.depends('thang', 'name')
    def _compute_name(self):
        for e in self:
            name = ""
            if e.thang:
                name += e.thang
            if e.nam:
                name += '/' + e.nam
            e.name = name.upper()


    def func_thuchien_chamcong_theo_ngay(self, ngay):
        chamcongs = self.env['ekids.chamcong_giaovien2thang'].search(
                    [
                        ('coso_id', '=', self.coso_id.id),
                        ('chamcong_loai2thang_id', '=', self.id)

                    ])
        if chamcongs:
            for gv_chamcong in chamcongs:
                field_name = f'd{ngay}'
                setattr(gv_chamcong, field_name, True)

    def action_open_popup_luachon_ngay_chamcong(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHẤM CÔNG',
            'res_model': 'ekids.chamcong_ngay_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context':
                {'default_loai2thang_id': self.id,
                 'default_coso_id': self.coso_id.id
                 }
        }

    def func_tao_macdinh_chamcong(self):
        days = ngay_util.func_get_cacngay_trong_thang(int(self.nam), int(self.thang))
        ngay_dauthang = days[0]
        ngay_cuoithang = days[len(days) - 1]
        nam = ngay_dauthang.year
        thang = ngay_dauthang.month
        giaoviens = giaovien_util.func_get_giaoviens_trong_thang(self, self.coso_id.id, nam, thang)
        if giaoviens:
            nghiles = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, self.coso_id, None, ngay_dauthang,
                                                                         ngay_cuoithang)
            coso_hoatdongs = coso_util.func_get_ngay_hoatdongs(self.coso_id, nam,thang)
            nghipheps = giaovien_util.func_get_nghipheps_tatca_giaovien(self, self.coso_id, nam, thang)

            for giaovien in giaoviens:
                if self.chamcong_loai_id.loai =='1':
                    #KPI
                    self.func_tao_macdinh_kpi_cho_giaovien(giaovien)
                elif self.chamcong_loai_id.loai =='0':
                    # ĐI LÀM
                    self.func_tao_macdinh_chamcong_cho_giaovien(giaovien,coso_hoatdongs,nghiles,nghipheps)
                elif self.chamcong_loai_id.loai == '2':
                    # CÔNG VIỆC
                    is_default_ok =self.chamcong_loai_id.dm_chamcong_id.is_default_ok
                    self.func_tao_macdinh_congviec_cho_giaovien(giaovien,is_default_ok)
                else:
                    # CÔNG VIỆC GIÁ TRỊ
                    self.func_tao_macdinh_congviec_giatri_cho_giaovien(giaovien, coso_hoatdongs, nghiles, nghipheps)


    def func_tao_macdinh_chamcong_cho_giaovien(self,giaovien,coso_hoatdongs,nghiles,nghipheps):
        giaovien2thang = self.env['ekids.chamcong_giaovien2thang'].search(
            [
                ('coso_id', '=', self.coso_id.id),
                ('chamcong_loai2thang_id', '=', self.id),
                ('giaovien_id', '=', giaovien.id)
            ],limit=1)
        if not giaovien2thang:
            data = {
                "coso_id": self.coso_id.id,
                "chamcong_loai2thang_id": self.id,
                "giaovien_id": giaovien.id

            }
            giaovien2thang =self.env['ekids.chamcong_giaovien2thang'].create(data)
        giaovien2thang.func_tinhtoan_giatri_giaovien2thang(nghiles,coso_hoatdongs,nghipheps)
        giaovien2thang.func_tinhtoan_cac_giatri_tong()

    def func_tao_macdinh_congviec_cho_giaovien(self,giaovien,is_default_ok):
        giaovien2thang = self.env['ekids.chamcong_congviec2thang'].search(
            [
                ('coso_id', '=', self.coso_id.id),
                ('chamcong_loai2thang_id', '=', self.id),
                ('giaovien_id', '=', giaovien.id)
            ],limit=1)
        if not giaovien2thang:
            data = {
                "coso_id": self.coso_id.id,
                "chamcong_loai2thang_id": self.id,
                "giaovien_id": giaovien.id

            }
            if is_default_ok ==True:
                for day in range(1, 32):  # từ 1 đến 32
                    field_name = "d"+str(day)
                    data[field_name]= True

            giaovien2thang =self.env['ekids.chamcong_congviec2thang'].create(data)

    def func_tao_macdinh_congviec_giatri_cho_giaovien(self,giaovien,coso_hoatdongs,nghiles,nghipheps):
        giaovien2thang = self.env['ekids.chamcong_congviec2thang_giatri'].search(
            [
                ('coso_id', '=', self.coso_id.id),
                ('chamcong_loai2thang_id', '=', self.id),
                ('giaovien_id', '=', giaovien.id)
            ],limit=1)
        if not giaovien2thang:
            data = {
                "coso_id": self.coso_id.id,
                "chamcong_loai2thang_id": self.id,
                "giaovien_id": giaovien.id

            }
            giaovien2thang =self.env['ekids.chamcong_congviec2thang_giatri'].create(data)


    def func_tao_macdinh_kpi_cho_giaovien(self,giaovien):
        count = self.env['ekids.chamcong_kpi2thang'].search_count(
            [
                ('coso_id', '=', self.coso_id.id),
                ('chamcong_loai2thang_id', '=', self.id),
                ('giaovien_id', '=', giaovien.id)
            ])
        if count <=0:
            data ={
                "coso_id":self.coso_id.id,
                "chamcong_loai2thang_id": self.id,
                "giaovien_id":giaovien.id,

            }
            self.env['ekids.chamcong_kpi2thang'].create(data)

    def action_vao_chamcong_theoloai(self):
        self.func_tao_macdinh_chamcong()
        name = str(self.thang) + "/" + str(self.nam)
        if self.chamcong_loai_id.dm_chamcong_id.loai =='1':
            return self.func_call_kpi2thang()
        elif self.chamcong_loai_id.dm_chamcong_id.loai =='0':
            return  self.func_call_giaovien2thang()
        elif self.chamcong_loai_id.dm_chamcong_id.loai == '2':
            return self.func_call_congviec2thang()
        else:
            return self.func_call_congviec2thang_giatri()




    def func_call_kpi2thang(self):

        name = "THÁNG "+str(self.thang) + "/" + str(self.nam)
        return {
            'type': 'ir.actions.act_window',
            'name': name.upper(),
            'res_model': 'ekids.chamcong_kpi2thang',
            'view_mode': 'list',
            'target': 'current',
            'domain': [
                ('coso_id', '=', self.coso_id.id),
                ('chamcong_loai2thang_id', '=', self.id)
            ],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_chamcong_loai_id': self.id,
                'default_nam': self.nam,
                'default_thang': self.thang
            },
        }

    def func_call_giaovien2thang(self):
        name = "THÁNG "+str(self.thang) + "/" + str(self.nam)
        return {
            'type': 'ir.actions.act_window',
            'name': name.upper(),
            'res_model': 'ekids.chamcong_giaovien2thang',
            'view_mode': 'list',
            'domain': [
                ('coso_id', '=', self.coso_id.id),
                ('chamcong_loai2thang_id', '=', self.id),
            ],
            'target': 'current',
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_chamcong_loai_id': self.id,
                'default_nam': self.nam,
                'default_thang': self.thang
            },
        }

    def func_call_congviec2thang(self):
        name = "THÁNG "+str(self.thang) + "/" + str(self.nam)
        return {
            'type': 'ir.actions.act_window',
            'name': name.upper(),
            'res_model': 'ekids.chamcong_congviec2thang',
            'view_mode': 'list',
            'domain': [
                ('coso_id', '=', self.coso_id.id),
                ('chamcong_loai2thang_id', '=', self.id),
            ],
            'target': 'current',
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_chamcong_loai2thang_id': self.id,
                'default_nam': self.nam,
                'default_thang': self.thang
            },
        }

    def func_call_congviec2thang_giatri(self):
        name = "THÁNG "+str(self.thang) + "/" + str(self.nam)
        return {
            'type': 'ir.actions.act_window',
            'name': name.upper(),
            'res_model': 'ekids.chamcong_congviec2thang_giatri',
            'view_mode': 'list',
            'domain': [
                ('coso_id', '=', self.coso_id.id),
                ('chamcong_loai2thang_id', '=', self.id),
            ],
            'target': 'current',
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_chamcong_loai_id': self.id,
                'default_nam': self.nam,
                'default_thang': self.thang
            },
        }