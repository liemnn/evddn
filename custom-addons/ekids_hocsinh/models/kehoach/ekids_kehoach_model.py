from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from .abstractmodel.ekids_kehoach_button_abstractmodel import KeHoachButtonAbstractModel
from .abstractmodel.ekids_kehoach_action_abstractmodel import  KeHoachActionAbstractModel
from .abstractmodel.ekids_kehoach_taomoi_abstractmodel import KeHoachTaoMoiAbstractModel


from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class KeHoachCanThiep(models.Model
        ,KeHoachButtonAbstractModel
        ,KeHoachActionAbstractModel
        ,KeHoachTaoMoiAbstractModel):

    _name = "ekids.kehoach"
    _description = "Kế hoạch can thiệp cho trẻ"

    sequence = fields.Integer(string="STT", default=10)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", readonly=True)
    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh")
    tu_ngay = fields.Date(string="Sẽ can thiệp từ ngày")
    sothang = fields.Selection([("1", "1 Tháng"),
                                        ("2", "2 Tháng"),
                                        ("3", "3 Tháng"),
                                        ("4", "4 Tháng"),
                                        ("5", "5 Tháng"),
                                        ("6", "6 Tháng"),
                                        ("7", "7 Tháng"),
                                        ("8", "8 Tháng"),
                                        ("9", "9 Tháng"),
                                        ("10", "10 Tháng"),
                                        ("11", "11 Tháng"),
                                        ("12", "12 Tháng")],
                               compute="_compute_kehoach_sothang",store=True,string="Số tháng lập [Kế hoạch]")
    den_ngay = fields.Date(string="Can thiệp đến ngày",compute="_compute_kehoach_denngay"
                           ,store=True,readonly=True)
    name = fields.Char(string="Tên",compute="_compute_kehoach_name",readonly=True)
    ketluan_id = fields.Many2one("ekids.ketluan",
                                 string="Lựa chọn [Kết luận Đánh giá] để cho lập kế hoạch")
    is_co_ketluan =fields.Boolean(string="Có kết luận",compute="_compute_is_co_ketluan",readonly=True)

    gv_lapkehoach_id = fields.Many2one("ekids.giaovien", compute="_compute_kehoach_giaovien",
                                       string="Giáo viên [Lập kế hoạch]",store=True, readonl=True)
    gv_canthiep_id = fields.Many2one("ekids.giaovien",
                                     string="Giáo viên phụ trách [Can thiệp]" ,store=True, readonl=True)



    trangthai = fields.Selection([("0", "Đang lập [Kế hoach khung]")
                                     ,("1", "Đã gửi [Kế hoach khung] cho Giáo viên Can thiệp ")
                                     ,("2", "Đang [Can thiệp]")
                                     ,("3", "Đã kết thúc [Can thiệp]")], string="Trạng thái [Kế hoạch]"
                                    ,default="0")



    mau_kehoach_id = fields.Many2one("ekids.mau_kehoach", string="Mấu đã chọn cho [Kế hoạch]")

    is_sudung_mau = fields.Boolean(string="Lập kế hoạch từ [Mẫu] có sẵn")


    is_gui_pheduyet = fields.Boolean (string="Gửi phê duyệt",
            compute='_compute_is_gui_pheduyet',
            store=False)

    is_keolai_lap_kehoach = fields.Boolean(string="Kéo lại trạng thái Lập kế hoạch",
                                     compute='_compute_is_keolai_lap_kehoach',
                                     store=False)


    is_ketthuc = fields.Boolean(string="Kết thúc quá trình [Can thiệp]",
                                 compute='_compute_is_ketthuc',
                                 store=False)

    is_lapkehoach = fields.Boolean(string="Lập kế hoach",
                                compute='_compute_is_lapkehoach',
                                store=False)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['trangthai'] = '0'
        return super(KeHoachCanThiep, self).create(vals_list)


    @api.depends('ketluan_id')
    def _compute_is_co_ketluan(self):
        for record in self:
            if record.ketluan_id:
                record.is_co_ketluan =True
            else:
                record.is_co_ketluan = False
    def _compute_kehoach_name(self):
        for kh in self:
            if kh.tu_ngay and kh.den_ngay and kh.sothang:
                kh.name = ('KẾ HOẠCH '+str(kh.sothang)+' Tháng (Từ:'+str(kh.tu_ngay.strftime("%d/%m/%Y"))
                           +' Đến:'+str(kh.den_ngay.strftime("%d/%m/%Y"))+')')
            else:
                kh.name = ""

    @api.depends("ketluan_id")
    def _compute_kehoach_giaovien(self):
        for kh in self:
            if kh.ketluan_id:
                if (kh.ketluan_id.gv_lapkehoach_id
                        and kh.ketluan_id.gv_canthiep_id):
                    kh.gv_lapkehoach_id = kh.ketluan_id.gv_lapkehoach_id
                    kh.gv_canthiep_id = kh.ketluan_id.gv_canthiep_id


    @api.depends("tu_ngay", "sothang")
    def _compute_kehoach_denngay(self):
        for kh in self:
            if kh.tu_ngay and kh.sothang:
                try:
                    sothang = int(kh.sothang) + 1
                    kh.den_ngay = kh.tu_ngay + timedelta(days=(sothang * 30))
                except Exception as e:
                    kh.den_ngay = None
            else:
                kh.den_ngay = None  # PHẢI gán để tránh lỗi

    @api.depends("mau_kehoach_id")
    def _compute_kehoach_sothang(self):
        for record in self:
            if record.mau_kehoach_id:
                mau=self.env['ekids.mau_kehoach'].browse(record.mau_kehoach_id.id)
                if mau:
                    record.sothang = mau.sothang
                else:
                    record.sothang = 0
            else:
                record.sothang = 0





    def action_xem_kehoach_hocsinh_thang_phucvu_canthiep(self):
       self.ensure_one()
       kanban_view_id = self.env.ref('ekids_hocsinh.kehoach_thang_canthiep_kanban_view').id
       return {
            'type': 'ir.actions.act_window',
            'name': 'KẾ HOẠCH CAN THIỆP [THÁNG]',
            'res_model': 'ekids.kehoach_thang',
            'view_mode': 'kanban,list',
            'views': [
               (kanban_view_id, 'kanban'),

            ],
            'target': 'current',
            'domain': [('kehoach_id','=',self.id)],
            'context': dict(
                self.env.context,
                default_kehoach_id=self.id,
            ),
        }


    def action_luachon_mau_kehoach(self):
        self.ensure_one()

        chinh_dm_roiloan_id = False
        dikem_dm_roiloan_ids = []
        gioitinh=False
        dm_tuoi_id=False

        if self.ketluan_id.chinh_dm_roiloan_id.exists():
            chinh_dm_roiloan_id = self.ketluan_id.chinh_dm_roiloan_id.id
        if self.ketluan_id.roiloan2dikem_ids:
            dikem_dm_roiloan_ids=self.ketluan_id.roiloan2dikem_ids.ids
        if self.hocsinh_id.gioitinh:
            gioitinh = self.hocsinh_id.gioitinh
        if self.ketluan_id.dm_tuoi_id:
            dm_tuoi_id= self.ketluan_id.dm_tuoi_id.id



        return {
            'type': 'ir.actions.act_window',
            'name': 'Lựa chọn mẫu cho [Kế hoạch]',
            'res_model': 'ekids.kehoach_timkiem_mau2kehoach',
            'view_mode': 'form',
            'target': 'new',
            'fullscreen': True,
            'context': dict(
                self.env.context,
                default_chinh_dm_roiloan_id=chinh_dm_roiloan_id,
                default_dikem_dm_roiloan_ids=dikem_dm_roiloan_ids,
                default_kehoach_id=self.id,
                kehoach_id=self.id,
                default_gioitinh=gioitinh,
                default_dm_tuoi_id=dm_tuoi_id
            ),
        }

    def action_xoabo_mau_kehoach(self):
        for record in self:
            record.mau_kehoach_id = False













