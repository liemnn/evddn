from odoo import models, fields, api, _
from .ekids_diemdanh_hocsinh2thang_abstractmodel import DiemDanhHocSinh2ThangAbstractModel
from odoo.exceptions import UserError
from datetime import datetime,date,timedelta

from odoo.exceptions import ValidationError
import calendar

import logging
_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")




class DiemDanhHocSinh2Thang(models.Model,DiemDanhHocSinh2ThangAbstractModel):
    _name = "ekids.diemdanh_hocsinh2thang"
    _description = "Điểm danh học sinh theo học"

    sequence = fields.Integer(string="TT", compute="_compute_sequence")
    coso_id = fields.Many2one("ekids.coso", related="diemdanh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")

    diemdanh_id = fields.Many2one("ekids.diemdanh", string="Thuộc"
                                  ,index=True,required=True, ondelete="cascade")

    hocsinh_id = fields.Many2one('ekids.hocsinh', string="Họ và tên",
                                 domain="[('coso_id','=',coso_id)]",required=True)



    # --- sinh tự động các field d1..d31 và is_d1_nghi..is_d31_nghi ---
    # sinh field d1..d31 và is_d1_nghi..is_d31_nghi
    options = [("-1", "Nghỉ không phép"),
               ("0", "Học nửa buổi"),
               ('1', "Đi học"),
               ('11', "Đi học - Có ca [Học bù /Tăng cường]"),
               ('10', "Không đăng ký học -Nghỉ"),
               ('2', "Nghỉ lễ"),
               ('3', "Nhà trường cho nghỉ"),
               ('4', "Học sinh nghỉ có phép")]

    for day in range(1, 32):
        locals()[f'd{day}'] = fields.Selection(
            selection=options,
            string=str(day),
            required=True,
            default="1"
        )
        locals()[f'is_d{day}_nghi'] = fields.Boolean(
            string="Nghỉ",
            compute="_compute_all_is_d_nghi",
            store=False,
            default=True
        )
    tong_dihoc_kehoach = fields.Integer(string="Đi Học kế hoạch")
    tong_dihoc_coso = fields.Integer(string="Đi Học theo Cơ sở")
    tong_dihoc_diemdanh = fields.Integer(string="Đi học được chấm công")
    tong_nghiphep = fields.Integer(string="Nghỉ phép")
    tong_nghi_cangay = fields.Integer(string="Nghỉ cả ngày")
    tong_dihoc_nuabuoi = fields.Integer(string="Nghỉ nửa buổi")

    hocbu_thangtruoc = fields.Integer(string="Còn lại tháng trước", default=0)
    hocbu_thangnay = fields.Integer(string="Cộng dồn đến hôm nay", default=0)
    hocbu_da_day = fields.Integer(string="Đã dạy bù thêm trong tháng này", default=0)
    tangcuong_da_day = fields.Integer(string="Ca tăng cường trong tháng", default=0)
    hocbu_conlai = fields.Integer(string="Số ca [Học bù] còn lại",
                                  compute="_compute_hocbu_conlai",
                                  default=0)

    hocbu_thangnay_ids = fields.One2many("ekids.diemdanh_ca2ngay",
                                           compute="_compute_hocbu_thangnay_ids",
                                           string="Học bù")

    hocbu_da_day_ids = fields.One2many("ekids.diemdanh_ca2ngay",
                                         compute="_compute_hocbu_da_day_ids",
                                         string="Học bù")
    tangcuong_ids = fields.One2many("ekids.diemdanh_ca2ngay",
                                       compute="_compute_tangcuong_ids",
                                       string="Tăng cường")
    field_sua = fields.Char("Các trường do người dùng điều chỉnh",default="")


    def _compute_sequence(self):
        index =1
        for record in self:
            record.sequence = index
            index +=1
    @api.depends('hocbu_thangtruoc')
    def _compute_hocbu_conlai(self):
        nam = self.diemdanh_id.nam
        thang = self.diemdanh_id.thang
        days = ngay_util.func_get_cacngay_trong_thang(int(nam), int(thang))
        ngay_dauthang = days[0]
        ngay_cuoithang = days[len(days) - 1]

        for rec in self:
            count_ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search_count([
                ('hocsinh_id', '=', rec.hocsinh_id.id),
                ('trangthai', '=', '3'),
                ('ngay', '>=', ngay_dauthang),
                ('ngay', '<=', ngay_cuoithang)
            ])

            rec.hocbu_thangnay = count_ca2ngay_ids +rec.hocbu_thangtruoc

            count_ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search_count([
                ('hocsinh_id', '=', rec.hocsinh_id.id),
                ('trangthai', '=', '4'),
                ('ngay', '>=', ngay_dauthang),
                ('ngay', '<=', ngay_cuoithang)
            ])

            rec.hocbu_da_day =count_ca2ngay_ids
            rec.hocbu_conlai = rec.hocbu_thangnay- rec.hocbu_da_day

            count_ca2ngay_tc= self.env['ekids.diemdanh_ca2ngay'].search_count([
                ('hocsinh_id', '=', rec.hocsinh_id.id),
                ('trangthai', '=', '5'),
                ('ngay', '>=', ngay_dauthang),
                ('ngay', '<=', ngay_cuoithang)
            ])
            rec.tangcuong_da_day = count_ca2ngay_tc



    def _compute_hocbu_thangnay_ids(self):
        nam = self.diemdanh_id.nam
        thang = self.diemdanh_id.thang
        days = ngay_util.func_get_cacngay_trong_thang(int(nam),int(thang))
        ngay_dauthang =days[0]
        ngay_cuoithang= days[len(days)-1]
        for rec in self:
            # trang thai: nghi va se day bu
            ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search([
                ('hocsinh_id', '=', rec.hocsinh_id.id),
                ('trangthai', '=', '3'),
                ('ngay', '>=', ngay_dauthang),
                ('ngay', '<=', ngay_cuoithang)
            ])

            rec.hocbu_thangnay_ids =ca2ngay_ids


    @api.depends( 'hocbu_da_day_ids')
    def _compute_hocbu_da_day_ids(self):
        nam = self.diemdanh_id.nam
        thang = self.diemdanh_id.thang
        days = ngay_util.func_get_cacngay_trong_thang(int(nam),int(thang))
        ngay_dauthang =days[0]
        ngay_cuoithang= days[len(days)-1]
        for rec in self:
            # trang thai: nghi va se day bu
            ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search([
                ('hocsinh_id', '=', rec.hocsinh_id.id),
                ('trangthai', '=', '4'),
                ('ngay', '>=', ngay_dauthang),
                ('ngay', '<=', ngay_cuoithang)
            ])

            rec.hocbu_da_day_ids =ca2ngay_ids

    @api.depends('tangcuong_ids')
    def _compute_tangcuong_ids(self):
        nam = self.diemdanh_id.nam
        thang = self.diemdanh_id.thang
        days = ngay_util.func_get_cacngay_trong_thang(int(nam), int(thang))
        ngay_dauthang = days[0]
        ngay_cuoithang = days[len(days) - 1]
        for rec in self:
            # trang thai: nghi va se day bu
            ca2ngay_ids = self.env['ekids.diemdanh_ca2ngay'].search([
                ('hocsinh_id', '=', rec.hocsinh_id.id),
                ('trangthai', '=', '5'),
                ('ngay', '>=', ngay_dauthang),
                ('ngay', '<=', ngay_cuoithang)
            ])

            rec.tangcuong_ids = ca2ngay_ids


    def _compute_all_is_d_nghi(self):
        today =date.today()
        for record in self:
            ngay_nhaphoc = record.hocsinh_id.ngay_nhaphoc
            ngay_nghihoc = record.hocsinh_id.ngay_nghihoc
            for day in range(1, 32):  # từ 1 đến 32
                field_name = f'is_d{day}_nghi'
                try:
                    thang = int(record.diemdanh_id.thang)
                    nam =int(record.diemdanh_id.nam)
                    ngay =date(nam,thang,day)
                    weekday = ngay.weekday() + 2
                    thu_field = 'hd_t' + str(weekday)
                    is_hoc = getattr(record.coso_id, thu_field)
                    is_hoatdong = False
                    if is_hoc:
                        if ngay > today:
                            is_hoatdong =True
                        elif (ngay_nghihoc and ngay_nghihoc<ngay):
                            is_hoatdong =True
                        else:
                            if ngay <ngay_nhaphoc:
                                is_hoatdong =True
                            else:
                                is_hoatdong = False
                    else:
                        is_hoatdong = True

                    setattr(record, field_name, is_hoatdong)


                except ValueError:
                    setattr(record,field_name,True)


    def func_tinhtoan_giatri_hocsinh2ngay(self,nghiles,coso_hoatdongs,nghipheps,ca_tangcuongs,is_create):
        today = date.today()
        thang = int(self.diemdanh_id.thang)
        nam = int(self.diemdanh_id.nam)
        hocsinh = self.hocsinh_id
        is_blocked = ngay_util.func_is_blocked(nam,thang)
        for day in range(1, 32):  # từ 1 đến 32
            field_ngay_giatri = f'd{day}'
            if is_blocked == True:
                continue
            try:
                ngay = date(nam,thang,day)
                weekday =ngay.weekday()+2
                field_hs = "hd_t"+str(weekday)
                is_hs_hoc = getattr(hocsinh,field_hs)
                giatri_old = getattr(self,field_ngay_giatri)
                if (coso_hoatdongs.get(ngay) == False
                        or giatri_old == '0'
                        or giatri_old == '-1'):
                    continue
                elif (hocsinh.is_ngaydihoc_rieng==True and is_hs_hoc ==False):
                    key = "["+str(ngay)+"]"
                    if (self.field_sua != None and (key in str(self.field_sua))):
                        continue
                    else:
                        setattr(self, field_ngay_giatri, "10")
                        value =str(self.field_sua) + key
                        setattr(self, "field_sua", value)

                else:
                    giatri_new = self.func_is_tinhtoan_giatri_moi(ngay,nghiles,coso_hoatdongs,nghipheps,ca_tangcuongs)
                    if giatri_new != giatri_old:
                        setattr(self, field_ngay_giatri, giatri_new)
            except ValueError:
                loi=1


    def func_is_tinhtoan_giatri_moi(self,ngay,nghiles,coso_hoatdongs,nghipheps,ca_tangcuongs):
        giatri = '1'
        is_hoatdong =coso_hoatdongs.get(str(ngay))
        if is_hoatdong == True:
            nghile = nghiles.get(str(ngay))
            if nghile:
                if nghile.loai == '0':
                    giatri = '2'
                else:
                    giatri = '3'
            else:
                key = str(self.hocsinh_id.id) + ":" + str(ngay)
                if nghipheps.get(key):
                    giatri = "4"
                else:
                    is_tangcuong = self.func_is_co_ca_hocbu_tangcuong(ca_tangcuongs,self.hocsinh_id.id,ngay)
                    if is_tangcuong ==True:
                        giatri="11"
                    is_ca_ngay =hocsinh_util.func_is_co_ca_trong_ngay(self.hocsinh_id,ngay)
                    if is_ca_ngay == False:
                        giatri="10"

        return giatri


    def func_is_co_ca_hocbu_tangcuong(self,ca_tangcuongs,hocsinh_id,ngay):
        if ca_tangcuongs:
            key = str(hocsinh_id)+":" +str(ngay)
            ca = ca_tangcuongs.get(key)
            if ca:
                return True
        return False









    def action_open_popup_thongtin_diemdanh_hocsinh(self):
        self.ensure_one()
        self.func_tinhtoan_tong()
        form_view_id = self.env.ref('ekids_diemdanh.diemdanh_hocsinh2thang_form').id  # chú ý id chính xác

        return {
            'type': 'ir.actions.act_window',
            'name': 'THÔNG TIN [HỌC BÙ/DẠY BÙ]',
            'res_model': 'ekids.diemdanh_hocsinh2thang',
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,

            ),
        }
    def func_tinhtoan_tong(self):
        tong_dihoc_diemdanh = 0
        tong_nghiphep = 0
        tong_nghi_cangay = 0
        tong_dihoc_nuabuoi = 0
        options = [("-1", "Nghỉ không phép"),
                   ("0", "Học nửa buổi"),
                   ('1', "Đi học"),
                   ('2', "Nghỉ lễ"),
                   ('3', "Nhà trường cho nghỉ"),
                   ('4', "Học sinh nghỉ có phép")]
        for day in range(1, 32):
            field_name = "d" + str(day)
            giatri = getattr(self, field_name)
            if giatri == '-1':
                # nghi
                tong_nghi_cangay += 1
            elif giatri == '0':
                tong_dihoc_nuabuoi += 1
            elif giatri == '1' or giatri =="11":
                tong_dihoc_diemdanh += 1
            elif giatri == '4' :
                tong_nghiphep += 1
            else:
                continue
        thang = int(self.diemdanh_id.thang)
        nam = int(self.diemdanh_id.nam)
        days = ngay_util.func_get_cacngay_trong_thang(nam,thang)
        ngay_dauthang =days[0]
        ngay_cuoithang = days[len(days)-1]

        if ngay_dauthang < self.hocsinh_id.ngay_nhaphoc:
            ngay_dauthang = self.hocsinh_id.ngay_nhaphoc

        nghiles_all = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, self.coso_id, None, ngay_dauthang, ngay_cuoithang)
        coso_nghiles = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, self.coso_id, '0', ngay_dauthang,
                                                                         ngay_cuoithang)

        ngay_dihoc_kehoachs = hocsinh_util.func_get_ngay_dihoc_kehoachs(self.coso_id,coso_nghiles,self.hocsinh_id,ngay_dauthang,ngay_cuoithang)
        ngay_dihoc_cosos= hocsinh_util.func_get_ngay_dihoc_cua_coso(self.coso_id, coso_nghiles, ngay_dauthang,ngay_cuoithang)

        self.tong_dihoc_kehoach = len(ngay_dihoc_kehoachs)
        self.tong_dihoc_coso = len(ngay_dihoc_cosos)
        ngay_dihoc_thucte =hocsinh_util.func_get_ngay_dihoc_thucte(self,self, nghiles_all)
        self.tong_dihoc_diemdanh = len(ngay_dihoc_thucte)
        self.tong_nghiphep = tong_nghiphep
        self.tong_nghi_cangay = tong_nghi_cangay
        self.tong_dihoc_nuabuoi = tong_dihoc_nuabuoi
    def action_xoa_taolai_diemdanh(self):
        context = self.env.context
        coso_id = context.get("default_coso_id")
        thang = context.get("default_thang")
        nam = context.get("default_nam")
        coso_util.func_check_errors(int(nam),int(thang))
        if thang and nam:
            diemdanhs = self.env['ekids.diemdanh'].search([
                ('coso_id', '=', coso_id)
                , ('nam', '=', nam)
                , ('thang', '=', thang)
            ])
            #B1: xoa di
            if diemdanhs:
                for diemdanh in diemdanhs:
                    diemdanh.unlink()
            #B2 tao moi
            data = {
                'coso_id': int(coso_id),
                'nam': str(nam),
                'thang': str(thang)
            }
            diemdanh = self.env['ekids.diemdanh'].create(data)
            if diemdanh:
                diemdanh.func_tao_macdinh_diemdanh_hocsinh2thang()
                if diemdanh:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'THÁNG[' + str(thang) + ']',
                        'res_model': 'ekids.diemdanh_hocsinh2thang',
                        'view_mode': 'list',
                        'target': 'current',
                        'domain': [
                            ('coso_id', '=', diemdanh.coso_id.id),
                            ('diemdanh_id', '=', diemdanh.id)
                        ],
                        'context': {
                            'default_coso_id': diemdanh.coso_id.id,
                            'default_thang': str(thang),
                            'default_nam': str(nam)
                        }
                    }









