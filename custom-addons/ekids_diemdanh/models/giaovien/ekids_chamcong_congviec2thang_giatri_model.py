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



class ChamCongCongViec2ThangGiaTri(models.Model,ChamCongFuncAbstractModel):
    _name = "ekids.chamcong_congviec2thang_giatri"
    _description = "Điểm danh học sinh theo học"
    _order = "giaovien_id asc"

    sequence = fields.Integer(string="TT", compute="_compute_sequence")
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True)
    name = fields.Char(string="Học sinh",compute="_compute_name")
    chamcong_loai2thang_id = fields.Many2one("ekids.chamcong_loai2thang", string="Thuộc",required=True, ondelete="cascade")
    giaovien_id = fields.Many2one('ekids.giaovien', string="Họ và tên",
                                 domain="[('coso_id','=',coso_id)]",required=True,ondelete="cascade")
    d1=fields.Float('1', digits=(6, 1))
    for day in range(1, 32):
        locals()[f'd{day}'] = fields.Float(
            string=str(day),
            digits=(6, 1),
            default=0)
        locals()[f'is_d{day}_nghi'] = fields.Boolean(
            string="Nghỉ",
            compute="_compute_all_is_d_nghi",
            store=False,
            default=True
        )

    tong = fields.Float(string="Tổng", compute="_compute_tong", digits=(10, 1),store=True,defaul=0)




    @api.depends(
        'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9', 'd10',
        'd11', 'd12', 'd13', 'd14', 'd15', 'd16', 'd17', 'd18', 'd19', 'd20',
        'd21', 'd22', 'd23', 'd24', 'd25', 'd26', 'd27', 'd28', 'd29', 'd30', 'd31'
    )
    def _compute_tong(self):
        for record in self:
            tong = 0.0
            for i in range(1, 32):
                giatri = getattr(record, f'd{i}')
                tong = tong + float(giatri)
            record.update({"tong":tong})


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
                    if ngay > today:
                        is_hoatdong = False
                    elif (dilam_denngay and ngay > dilam_denngay):
                        is_hoatdong = False
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
        if thang and nam:
            chamcong_loai2thang = self.env['ekids.chamcong_loai2thang'].search([
                ('coso_id', '=', coso_id)
                , ('nam', '=', nam)
                , ('thang', '=', thang)
                , ('chamcong_loai_id.dm_chamcong_id.loai', '=', '2')
            ])
            if chamcong_loai2thang:
                congviec2thang_ids = chamcong_loai2thang.congviec2thang_ids
                #B1 xoa
                if congviec2thang_ids:
                    for congviec2thang_id in congviec2thang_ids:
                        congviec2thang_id.unlink()
                #B2 tinh toan
                chamcong_loai2thang.func_tao_macdinh_chamcong()



    def action_mo_popup_chamcong_congviec2ngay_giatri(self, record_id=None, field_name=None, field_value='1'):
        if record_id is not None and field_name and field_value is not None:
            if self:
                thang = self.chamcong_loai2thang_id.thang
                nam = self.chamcong_loai2thang_id.nam
                ngay = field_name.lstrip("d")
                day = date(int(nam), int(thang), int(ngay))

                giatri = getattr(self,field_name)
                if giatri == 0:
                    giatri = 1



                # Tạo default các ca can thiệp theo ngày
                view_form_id = self.env.ref("ekids_diemdanh.chamcong_congviec2ngay_giatri_wizard_form").id
                return {
                        "type": "ir.actions.act_window",
                        "name": "Điểm danh ngày",
                        "res_model": "ekids.chamcong_congviec2ngay_giatri_wizard",
                        "view_id": view_form_id,
                        "view_mode": "form",
                        "views": [(view_form_id, "form")],
                        "target": "new",
                        "context": {
                            "default_congviec2thang_giatri_id": self.id,
                            'default_ngay': day,
                            'default_giatri':giatri
                        }
                    }





