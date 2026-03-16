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



class ChamCongCongViec2Thang(models.Model,ChamCongFuncAbstractModel):
    _name = "ekids.chamcong_congviec2thang"
    _description = "Điểm danh học sinh theo học"
    _order = "giaovien_id asc"

    sequence = fields.Integer(string="TT", compute="_compute_sequence")
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True)
    name = fields.Char(string="Học sinh",compute="_compute_name")
    chamcong_loai2thang_id = fields.Many2one("ekids.chamcong_loai2thang", string="Thuộc",required=True, ondelete="cascade")
    giaovien_id = fields.Many2one('ekids.giaovien', string="Họ và tên",
                                 domain="[('coso_id','=',coso_id)]",required=True,ondelete="cascade")
    d1 = fields.Boolean("1",default=False)
    is_d1_nghi = fields.Boolean(string="Nghỉ",compute="_compute_all_is_d_nghi")

    d2= fields.Boolean("2",default=False)
    is_d2_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d3 = fields.Boolean("3",default=False)
    is_d3_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d4 = fields.Boolean("4",default=False)
    is_d4_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d5 = fields.Boolean("5",default=False)
    is_d5_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d6 = fields.Boolean("6",default=False)
    is_d6_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d7 = fields.Boolean("7",default=False)
    is_d7_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d8 = fields.Boolean("8",default=False)
    is_d8_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d9 = fields.Boolean("9",default=False)
    is_d9_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d10 = fields.Boolean("10",default=False)
    is_d10_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d11 = fields.Boolean("11",default=False)
    is_d11_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d12 = fields.Boolean("12",default=False)
    is_d12_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d13 = fields.Boolean("13",default=False)
    is_d13_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d14 = fields.Boolean("14",default=False)
    is_d14_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d15 = fields.Boolean("15",default=False)
    is_d15_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d16 = fields.Boolean("16",default=False)
    is_d16_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d17= fields.Boolean("17",default=False)
    is_d17_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d18 = fields.Boolean("18",default=False)
    is_d18_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d19 = fields.Boolean("19",default=False)
    is_d19_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d20 = fields.Boolean("20",default=False)
    is_d20_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d21 = fields.Boolean("21",default=False)
    is_d21_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d22 = fields.Boolean("22",default=False)
    is_d22_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d23 = fields.Boolean("23",default=False)
    is_d23_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d24 = fields.Boolean("24",default=False)
    is_d24_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d25 = fields.Boolean("25",default=False)
    is_d25_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d26 = fields.Boolean("26",default=False)
    is_d26_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d27 = fields.Boolean("27",default=False)
    is_d27_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d28 = fields.Boolean("28",default=False)
    is_d28_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d29 = fields.Boolean("29",default=False)
    is_d29_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    d30 = fields.Boolean("30",default=False)
    is_d30_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")


    d31= fields.Boolean("31",default=False)
    is_d31_nghi = fields.Boolean(string="Nghỉ", compute="_compute_all_is_d_nghi")

    tong = fields.Float(string="Tổng", compute="_compute_tong", digits=(10, 1),store=True,defaul=0)
    tong_temps = fields.Float(string="Tổng tạm", digits=(10, 1),defaul=0)


    ca2ngay_daythay_ids = fields.One2many("ekids.chamcong_ca2ngay_daythay", "congviec2thang_id"
                                  , string="Thông tin dạy thay")

    tong_ca_daythay = fields.Integer(string="Tổng ca đã dạy thay trong tháng", compute="_compute_tong_ca_daythay", digits=(10, 1), defaul=0)
    is_ca_daythay = fields.Boolean("Có ca dạy thay")
    def action_capnhat_ketqua_tong(self):
        form_view_id = self.env.ref('ekids_diemdanh.chamcong_congviec2thang_form').id  # chú ý id chính xác
        self.tong_temps =self.tong
        return {
            'type': 'ir.actions.act_window',
            'name': 'KPI',
            'res_model': 'ekids.chamcong_congviec2thang',
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'target': 'new',
            'res_id': self.id,
            "context": {
                    "default_coso_id": self.coso_id.id,
                    'default_giaovien_id': self.giaovien_id.id,

                }
        }
    @api.depends("ca2ngay_daythay_ids")
    def _compute_tong_ca_daythay(self):
        for record in self:
            if record.ca2ngay_daythay_ids:
                record.tong_ca_daythay = len(record.ca2ngay_daythay_ids)
                record.is_ca_daythay = True
            else:
                record.tong_ca_daythay = 0
                record.is_ca_daythay = False


    @api.depends(
        'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9', 'd10',
        'd11', 'd12', 'd13', 'd14', 'd15', 'd16', 'd17', 'd18', 'd19', 'd20',
        'd21', 'd22', 'd23', 'd24', 'd25', 'd26', 'd27', 'd28', 'd29', 'd30', 'd31'
    )
    def _compute_tong(self):
        for record in self:
            thang =record.chamcong_loai2thang_id.thang
            nam = record.chamcong_loai2thang_id.nam
            coso = record.coso_id
            tong = 0
            for i in range(1, 32):
                try:
                    ngay =date(int(nam),int(thang),i)
                    weekday = ngay.weekday() + 2
                    field_hd = "hd_t" + str(weekday)
                    if getattr(coso,field_hd) ==True:
                        if getattr(record, f'd{i}') == True:
                            tong = tong + 1
                except ValueError:
                     error=1

            record.tong = tong

    def _compute_sequence(self):
        index =1
        for record in self:
            record.sequence = index
            index +=1

    def _compute_name(self):
        for record in self:
            if record.giaovien_id:
                record.name = record.giaovien_id.name
            else:
                record.name =""




    def _compute_all_is_d_nghi(self):
        nam = int(self.chamcong_loai2thang_id.nam)
        thang = int(self.chamcong_loai2thang_id.thang)
        is_blocked = ngay_util.func_is_blocked(nam, thang)
        days = ngay_util.func_get_cacngay_trong_thang(nam,thang)
        ngay_dauthang  =days[0]
        ngay_cuoithang = days[len(days)-1]
        nghiles = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, self.coso_id, None, ngay_dauthang, ngay_cuoithang)
        coso_hoatdongs =coso_util.func_get_ngay_hoatdongs(self.coso_id,nam,thang)
        nghipheps = giaovien_util.func_get_nghipheps_tatca_giaovien(self, self.coso_id,nam,thang)
        today =date.today()
        for record in self:
            for day in range(1, 32):  # từ 1 đến 32

                field_name = f'is_d{day}_nghi'
                try:
                    ngay =date(nam,thang,day)
                    dilam_tungay = record.giaovien_id.dilam_tungay
                    dilam_denngay = record.giaovien_id.dilam_denngay
                    is_hoatdong = True
                    if ngay >today:
                        is_hoatdong = False
                    elif ( dilam_denngay and  ngay > dilam_denngay):
                        is_hoatdong =False
                    elif ngay < dilam_tungay:
                        is_hoatdong = False
                    else:
                        is_hoatdong = coso_hoatdongs.get(str(ngay))
                        if is_hoatdong == True:
                            is_nghile = nghiles.get(str(ngay))
                            if is_nghile:
                                is_hoatdong = False
                            else:
                                key = str(record.giaovien_id.id)+":"+str(ngay)
                                is_giaovien_nghi = nghipheps.get(key)
                                if is_giaovien_nghi:
                                    is_hoatdong = False
                                else:
                                    is_hoatdong = True
                        else:
                            is_hoatdong = False
                    setattr(record, field_name, False if is_hoatdong else True)
                except Exception as e:
                    setattr(record, field_name, True)

    def action_xoa_taolai_congviec2thang(self):
        context = self.env.context
        coso_id = context.get("default_coso_id")
        thang = context.get("default_thang")
        nam = context.get("default_nam")
        coso_util.func_check_errors(int(nam), int(thang))
        chamcong_loai2thang_id = context.get("default_chamcong_loai2thang_id")
        if thang and nam:
            chamcong_loai2thangs = self.env['ekids.chamcong_loai2thang'].browse(chamcong_loai2thang_id)
            if chamcong_loai2thangs:
                for chamcong_loai2thang in chamcong_loai2thangs:
                    congviec2thang_ids = chamcong_loai2thang.congviec2thang_ids
                    #B1 xoa
                    if congviec2thang_ids:
                        for congviec2thang_id in congviec2thang_ids:
                            congviec2thang_id.unlink()
                    #B2 tinh toan
                    chamcong_loai2thang.func_tao_macdinh_chamcong()

    def write(self, vals):
        if 'tong_temps' in vals:
            vals['tong'] = vals['tong_temps']
        return super(ChamCongCongViec2Thang, self).write(vals)











