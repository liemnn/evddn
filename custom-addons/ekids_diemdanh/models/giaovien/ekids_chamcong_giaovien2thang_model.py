from odoo import models, fields, api, _
from odoo.exceptions import UserError

from datetime import date,datetime
from odoo.exceptions import ValidationError
import calendar
from .ekids_chamcong_giaovien2thang_abstractmodel import  ChamCongGiaoVien2ThangAbstractModel
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




class ChamCongGiaoVien2Thang(models.Model,ChamCongGiaoVien2ThangAbstractModel,ChamCongFuncAbstractModel):
    _name = "ekids.chamcong_giaovien2thang"
    _description = "Điểm danh học sinh theo học"
    _order = "giaovien_id asc"

    sequence = fields.Integer(string="TT", compute="_compute_sequence")
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True)
    name = fields.Char(string="Học sinh",compute="_compute_name")
    chamcong_loai2thang_id = fields.Many2one("ekids.chamcong_loai2thang", string="Thuộc",required=True, ondelete="cascade")
    giaovien_id = fields.Many2one('ekids.giaovien', string="Họ và tên",
                                 domain="[('coso_id','=',coso_id)]",required=True,ondelete="cascade")
    options = [("-1", "Nghỉ làm"),
               ("0", "Đi làm nửa buổi"),
               ('1', "Đi làm"),
               ('10', "Đi làm(đi muộn)"),
               ('11', "Không đăng ký đi làm"),
               ('2', "Nghỉ lễ"),
               ('3', "Nhà trường cho nghỉ"),
               ('4', "Giáo viên nghỉ phép")

               ]

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
    tong_dilam_kehoach = fields.Float(string="Đi làm kế hoạch",digits=(10, 1))
    tong_dilam_chamcong = fields.Float(string="Đi làm được chấm công",digits=(10, 1),compute="_compute_tong_dilam_chamcong",store=True)
    tong_dilam_muon = fields.Integer(string="Đi làm được chấm công (Nhưng đi muộn)")
    tong_nghiphep = fields.Float(string="Nghỉ phép",digits=(10, 1))
    tong_nghi_cangay = fields.Integer(string="Nghỉ cả ngày")
    tong_dilam_nuabuoi = fields.Integer(string="Nghỉ nửa buổi")


    phep_duocphep = fields.Integer(string="Số ngày được [nghỉ phép] trong năm nay")
    phep_da_sudung = fields.Integer(string="Ngày phép đã sử dụng")
    phep_con_trongnam = fields.Integer(string="Ngày phép con lại trong năm")

    field_sua = fields.Char("Các trường do người dùng điều chỉnh", default="")

    def _compute_sequence(self):
        index =1
        for record in self:
            record.sequence = index
            index +=1

    @api.depends(
        'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9', 'd10',
        'd11', 'd12', 'd13', 'd14', 'd15', 'd16', 'd17', 'd18', 'd19', 'd20',
        'd21', 'd22', 'd23', 'd24', 'd25', 'd26', 'd27', 'd28', 'd29', 'd30', 'd31'
    )
    def _compute_tong_dilam_chamcong(self):
        for record in self:
            record.tong_dilam_chamcong = record.tong_dilam_kehoach - (record.tong_nghi_cangay + record.tong_nghiphep+(record.tong_dilam_nuabuoi/2))

    def action_xem_thongtin_dilam(self):

        self.func_tinhtoan_cac_giatri_tong()

        form_view_id = self.env.ref('ekids_diemdanh.chamcong_giaovien2thang_form').id  # chú ý id chính xác

        return {
            'type': 'ir.actions.act_window',
            'name': 'THÔNG TIN [CHẤM CÔNG]',
            'res_model': 'ekids.chamcong_giaovien2thang',
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,

            ),
        }

    def func_tinhtoan_cac_giatri_tong(self):
        tong_dilam_muon = 0
        tong_nghiphep = 0
        tong_nghi_cangay = 0
        tong_dilam_nuabuoi = 0

        for day in range(1, 32):
            field_name = "d" + str(day)
            giatri = getattr(self, field_name)
            if giatri == '-1':
                # nghi
                tong_nghi_cangay += 1
            elif giatri == '0':
                # di lam nua buoi
                tong_dilam_nuabuoi += 1
            elif giatri == '10':
                # di lam muon
                tong_dilam_muon += 1
            elif giatri == '4':
                # nghi phep
                tong_nghiphep += 1
            else:
                continue

        # xác định ngày đi làm đầu tiên
        loai2thang = self.chamcong_loai2thang_id
        nam = int(loai2thang.nam)
        thang = int(loai2thang.thang)
        days = ngay_util.func_get_cacngay_trong_thang(nam, thang)
        ngay_dauthang = days[0]
        ngay_cuoithang = days[len(days) - 1]
        nghiles = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, self.coso_id,None, ngay_dauthang,
                                                                     ngay_cuoithang)
        nghipheps = (giaovien_util
                     .func_get_nghipheps_trong_khoang_thoigian(self, self.coso_id, self.giaovien_id, nghiles, '1', ngay_dauthang,
                                                               ngay_cuoithang))

        tong_dilam_kehoachs = giaovien_util.func_get_ngay_dilam_theo_kehoach(self, self.coso_id, nghiles, ngay_dauthang,
                                                                             ngay_cuoithang)
        tong_dilam_kehoach = len(tong_dilam_kehoachs)
        self.tong_dilam_kehoach = tong_dilam_kehoach
        dl_chamcong = giaovien_util.func_get_dulieu_chamcong_thucte_giaovien(self,tong_dilam_kehoachs,self.giaovien_id,nghiles,nghipheps,nam,thang)

        self.tong_dilam_chamcong = dl_chamcong['dilam_chamcong']
        self.tong_dilam_muon = dl_chamcong['dilam_muon']

        self.tong_nghi_cangay = dl_chamcong['dilam_nghi']
        self.tong_dilam_nuabuoi = dl_chamcong['dilam_muon']

        self.tong_nghiphep = tong_nghiphep
        self.phep_duocphep = self.giaovien_id.phep_duocphep
        self.phep_da_sudung = self.giaovien_id.phep_da_sudung
        self.phep_con_trongnam = self.giaovien_id.phep_con_trongnam



    def _compute_name(self):
        for record in self:
            if record.giaovien_id:
                record.name = record.giaovien_id.name
            else:
                record.name =""





    def _compute_all_is_d_nghi(self):
        today =date.today()
        for record in self:
            dilam_tungay = record.giaovien_id.dilam_tungay
            dilam_denngay = record.giaovien_id.dilam_denngay
            for day in range(1, 32):  # từ 1 đến 32
                field_name = f'is_d{day}_nghi'

                try:
                    thang = int(record.chamcong_loai2thang_id.thang)
                    nam =int(record.chamcong_loai2thang_id.nam)
                    ngay =date(nam,thang,day)
                    weekday = ngay.weekday() + 2
                    thu_field = 'hd_t' + str(weekday)
                    is_hoc = getattr(record.coso_id, thu_field)
                    is_hoatdong = False
                    if is_hoc:
                        if ngay > today:
                            is_hoatdong =True
                        elif (dilam_denngay and dilam_denngay <ngay):
                            #Giao vien da nghi lam
                            is_hoatdong =True
                        else:
                            if ngay < dilam_tungay:
                                is_hoatdong =True
                            else:
                                is_hoatdong = False
                    else:
                        is_hoatdong = True

                    setattr(record, field_name, is_hoatdong)

                except ValueError:
                    setattr(record,field_name,True)


    def func_tinhtoan_giatri_giaovien2thang(self,nghiles,coso_hoatdongs,nghipheps):
        today = date.today()
        thang = int(self.chamcong_loai2thang_id.thang)
        nam = int(self.chamcong_loai2thang_id.nam)
        is_blocked = ngay_util.func_is_blocked(nam, thang)
        giaovien =self.giaovien_id
        for day in range(1, 32):  # từ 1 đến 32
            field_ngay_giatri = f'd{day}'
            if is_blocked == True:
                continue
            try:
                ngay = date(nam,thang,day)
                weekday = ngay.weekday() + 2
                giatri_old = getattr(self,field_ngay_giatri)
                field_gv = "hd_t" + str(weekday)
                is_giaovien_hoc = getattr(giaovien, field_gv)
                if (coso_hoatdongs.get(ngay) == False
                        or giatri_old == '0'
                        or giatri_old =='-1'
                        or giatri_old =='-2'):

                    continue
                elif (giaovien.is_ngaydilam_rieng==True and is_giaovien_hoc ==False):
                    key = "[" + str(ngay) + "]"
                    if (self.field_sua != None and (key in str(self.field_sua))):
                        continue
                    else:
                        setattr(self, field_ngay_giatri, "11")
                        value = str(self.field_sua) + key
                        setattr(self, "field_sua", value)
                else:
                    giatri_new = self.func_is_tinhtoan_giatri_moi(ngay,nghiles,coso_hoatdongs,nghipheps)
                    if giatri_new != giatri_old:
                        setattr(self, field_ngay_giatri, giatri_new)
            except ValueError:
                loi=1
    def func_is_tinhtoan_giatri_moi(self,ngay,nghiles,coso_hoatdongs,nghipheps):
        giatri = '1'
        if coso_hoatdongs.get(str(ngay)) == True:
            nghile = nghiles.get(str(ngay))
            if nghile:
                if nghile.loai == '0':
                    giatri = '2'
                else:
                    giatri = '3'
            else:
                key = str(self.giaovien_id.id) + ":" + str(ngay)
                if nghipheps.get(key):
                    giatri = "4"
        return giatri


    def action_xoa_taolai_congviec2thang(self):
        context = self.env.context
        coso_id = context.get("default_coso_id")
        thang = context.get("default_thang")
        nam = context.get("default_nam")
        coso_util.func_check_errors(int(nam),int(thang))
        if thang and nam:
            chamcong_loai2thang = self.env['ekids.chamcong_loai2thang'].search([
                ('coso_id', '=', coso_id)
                , ('nam', '=', nam)
                , ('thang', '=', thang)
                , ('chamcong_loai_id.dm_chamcong_id.loai', '=', '0')
            ])

            if chamcong_loai2thang:
                #B1: xóa kpi
                kpi2thang_ids = chamcong_loai2thang.kpi2thang_ids
                if kpi2thang_ids:
                    for kpi2thang_id in kpi2thang_ids:
                        kpi2thang_id.unlink()
                #B2 xoa chấm công
                        # B1: xóa kpi
                giaovien2thang_ids = chamcong_loai2thang.giaovien2thang_ids
                if giaovien2thang_ids:
                    for giaovien2thang_id in giaovien2thang_ids:
                        giaovien2thang_id.unlink()

                # B3: xóa giao viec
                congviec2thang_ids = chamcong_loai2thang.congviec2thang_ids
                if congviec2thang_ids:
                    for congviec2thang_id in congviec2thang_ids:
                        congviec2thang_id.unlink()


                #B2 tinh toan
                chamcong_loai2thang.func_tao_macdinh_chamcong()






