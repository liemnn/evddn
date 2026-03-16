from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import calendar
import uuid
from .ekids_luong_func_abstractmodel import LuongFuncAbstractModel
from .ekids_luong_formula_abstractmodel import LuongFolmulaAbstractModel
class Luong(models.Model,LuongFuncAbstractModel,LuongFolmulaAbstractModel):
    _name = 'ekids.luong'
    _description = 'Luong Giáo viên'

    # Khai báo các trường dữ liệu
    sequence = fields.Integer(string="TT", compute="_compute_sequence")
    coso_id = fields.Many2one("ekids.coso", related="giaovien_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    giaovien_id = fields.Many2one('ekids.giaovien', string="Giáo viên",required=True,ondelete="restrict")
    thang_id = fields.Many2one('ekids.luong_thang', string='Tháng',required=True,ondelete="restrict")
    nam_id = fields.Many2one('ekids.luong_nam',related="thang_id.nam_id", string='Năm', required=True, ondelete="restrict")

    trangthai = fields.Selection([("-1", "Đang tính")
                                    ,("0", "Đã rà soát")
                                   , ("1", "Đã nhận lương")],default="-1")
    is_show_tinhtoan_lai = fields.Boolean(compute="_compute_is_show_tinhtoan_lai")

    tham_nien = fields.Float(string="Thâm niên(năm)", default=0, digits=(10, 1))
    ngaycong =fields.Char(string="Ngày công",compute="_compute_ngaycong")
    so_ngaycong_quydinh = fields.Integer(string="Ngày làm/tháng", default=0)
    so_ngaycong = fields.Float(string="Đi làm", default=0, digits=(10, 1))
    so_ngaynghi = fields.Float(string="Nghỉ", default=0, digits=(10, 1))

    luong = fields.Float(string='Thực lĩnh(vnđ)', digits=(10, 0),compute="compute_luong", store=True)
    nhatruong_chi = fields.Float(string='Thông tin', digits=(10, 0), compute="compute_nhatruong_chi", store=True)
    tong_nhatruong_chi = fields.Float(string='Nhà trường thực chi (vnđ)', digits=(10, 0),
                                      compute="compute_tong_nhatruong_chi", store=True)
    nhatruong_thuho = fields.Float(string='Thông tin', digits=(10, 0), compute="compute_nhatruong_thuho", store=True)

    luong_cong_ids = fields.One2many(
        'ekids.luong_hangmuc', 'luong_id',
        string='Khoản được cộng(+)',
        domain=[('loai', '=', '1')],
        context={'default_loai': '1'}
    )

    luong_tru_ids = fields.One2many(
        'ekids.luong_hangmuc', 'luong_id',
        string='Khoản bị trừ(-)',
        domain=[('loai', 'in', ['-1', '-2'])],
        context={'default_loai': '-1'}
    )

    nhatruong_chitra_ids = fields.One2many(
        'ekids.luong_hangmuc', 'luong_id',
        string='Nhà trường chi trả',
        domain=[('loai', '=', '0')],
        context={'default_loai': '0'}
    )

    luong_thongtin_ids = fields.One2many(
        'ekids.luong_hangmuc', 'luong_id',
        string='thông tin',
        domain=[('loai', '=', '2')],
        context={'default_loai': '2'}
    )

    tong_cong = fields.Float(string='Được cộng(+)', digits=(10, 0),compute="compute_tong_cong", store=True)
    tong_tru = fields.Float(string='Bị trừ(-)', digits=(10, 0), compute="compute_tong_tru", store=True)
    tong_thongtin = fields.Float(string='Thông tin', digits=(10, 0), compute="compute_tong_thongtin", store=True)
    tong_thongtin_2 = fields.Float(string='Thông tin', digits=(10, 0), compute="compute_tong_thongtin_2", store=True)




    # làm access token  để chia sẻ
    access_token = fields.Char(string="Thẻ truy cập nhanh")
    share_url = fields.Char("Chi sẻ Phiếu Lương(URL)", compute="_compute_share_url",store=True)

    @api.depends("nhatruong_chitra_ids.tien", "nhatruong_chitra_ids.loai")
    def compute_nhatruong_chi(self):
        for record in self:
            tong = 0
            nhatruong_chitra_ids = record.nhatruong_chitra_ids
            if nhatruong_chitra_ids:
                for nhatruong_chitra_id in nhatruong_chitra_ids:
                    if nhatruong_chitra_id.loai == '0':
                        tong += nhatruong_chitra_id.tien
            record.nhatruong_chi = tong
    @api.depends("luong_tru_ids.tien", "luong_tru_ids.loai")
    def compute_nhatruong_thuho(self):
        for record in self:
            tong =0
            luong_tru_ids =record.luong_tru_ids
            if luong_tru_ids:
                for luong_tru_id in  luong_tru_ids:
                    if  luong_tru_id.loai=='-2':
                        tong += luong_tru_id.tien
            record.nhatruong_thuho = tong




    def _compute_sequence(self):
        index =1
        for record in self:
            record.sequence = index
            index +=1

    @api.depends("trangthai")
    def _compute_is_show_tinhtoan_lai(self):

        for record in self:
            if record.trangthai == "-1":
                record.is_show_tinhtoan_lai = True
            else:
                record.is_show_tinhtoan_lai = False

    def _compute_ngaycong(self):
        for record in self:
            record.ngaycong = str(record.so_ngaycong)+"/"+str(record.so_ngaycong_quydinh)


    @api.depends("luong")
    def _compute_share_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for rec in self:
            rec.access_token = str(uuid.uuid4())
            rec.share_url = rec.access_token and f"{base_url}/phieuluong/{rec.access_token}" or False


    @api.depends("tong_cong", "tong_tru")
    def compute_luong(self):
        for luong in self:
            luong.luong =luong.tong_cong - luong.tong_tru

    @api.depends("luong", "tong_thongtin")
    def compute_tong_nhatruong_chi(self):
        for luong in self:
            luong.tong_nhatruong_chi =luong.luong + luong.tong_thongtin

    @api.depends("luong_cong_ids.tien", "luong_cong_ids.loai")
    def compute_tong_cong(self):
        for luong in self:
            tong = 0
            if luong.luong_cong_ids:
                for cong in luong.luong_cong_ids:
                    if cong.loai == '1':
                        tong += cong.tien
            luong.tong_cong = tong

    @api.depends("luong_tru_ids.tien", "luong_tru_ids.loai")
    def compute_tong_tru(self):
        for luong in self:
            tong = 0
            if luong.luong_tru_ids:
                for cong in luong.luong_tru_ids:
                    # Đã sửa: Tính tổng nếu loai là '-1' HOẶC '-2'
                    if cong.loai in ['-1', '-2']:
                        tong += cong.tien

            # Đã sửa: Việc gán kết quả phải nằm ngoài vòng lặp for
            luong.tong_tru = tong

    @api.depends("nhatruong_chitra_ids.tien", "nhatruong_chitra_ids.loai")
    def compute_tong_thongtin(self):
        for luong in self:
            if luong.nhatruong_chitra_ids:
                tong =0
                for cong in luong.nhatruong_chitra_ids:
                    if cong.loai == '0':
                        tong += cong.tien
                    luong.tong_thongtin = tong
            else:
                luong.tong_thongtin=0

    @api.depends("luong_thongtin_ids.tien", "luong_thongtin_ids.loai")
    def compute_tong_thongtin_2(self):
        for luong in self:
            if luong.luong_thongtin_ids:
                tong = 0
                for cong in luong.luong_thongtin_ids:
                    if cong.loai == '2':
                        tong += cong.tien
                    luong.tong_thongtin_2= tong
            else:
                luong.tong_thongtin_2 = 0


    def _get_report_values(self, docids, data=None):
        docs = self.env[self._name].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': self._name,
            'docs': docs,
        }

    def action_xacthuc_tinhlai_luong_theo_thang(self):
        context = self.env.context
        coso_id = context.get("default_coso_id")
        thang = context.get("default_thang")
        nam = context.get("default_nam")

        #B1 xóa toàn bộ học phí tháng này của co so
        luongs = self.env['ekids.luong'].search([
                ('coso_id', '=',coso_id),
                ('thang_id', '=',str(thang)),
                ('nam_id', '=', str(nam))
         ])
        if luongs:
            for luong in luongs:
                if luong.trangthai=='-1':
                    luong.unlink()

        # B2 Tao lai default
        luong_thang= self.env['ekids.luong_thang'].search([
            ('coso_id', '=', coso_id),
            ('name', '=', str(thang)),
            ('nam_id', '=', str(nam))
        ])
        if luong_thang:
            luong_thang.action_view_khoitao_luong_giaovien()


    def action_in_luong(self):
        """Gọi report đã khai báo"""
        return (self.env.ref("ekids_giaovien.action_phieuluong")
                .report_action(self))

    def action_chuyen_trangthai(self,trangthai):
        for record  in self:
            record.write({'trangthai': trangthai})

    def action_xacthuc_tinhlai_luong_giaovien(self):
        #B1: xoa dữ liệu cũ
        luong_cong_ids = self.luong_cong_ids
        if luong_cong_ids:
            for luong_cong_id in luong_cong_ids:
                luong_cong_id.unlink()
        luong_tru_ids = self.luong_tru_ids
        if luong_tru_ids:
            for luong_tru_id in luong_tru_ids:
                luong_tru_id.unlink()
        luong_thongtin_ids = self.luong_thongtin_ids
        if luong_thongtin_ids:
            for luong_thongtin_id in luong_thongtin_ids:
                luong_thongtin_id.unlink()
        nhatruong_chitra_ids = self.nhatruong_chitra_ids
        if nhatruong_chitra_ids:
            for nhatruong_chitra_id in nhatruong_chitra_ids:
                nhatruong_chitra_id.unlink()


        self.func_tinhtoan_lai_luong_cho_mot_giaovien()
