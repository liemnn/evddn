from odoo import models, fields, api
from datetime import  timedelta,date

from odoo.exceptions import UserError, AccessError

from .ekids_kehoach_copy_abstractmodel import KeHoachCopyAbstractModel



import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")




class KeHoach(models.Model,KeHoachCopyAbstractModel):
    _name = 'ekids.kehoach'
    _description = 'Kết luận Đánh giá & Định hướng Kế hoạch'
    _order = 'tu_ngay desc, id desc'

    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    index = fields.Integer(string="STT", default=1, compute="_compute_index")
    # 1. THÔNG TIN HỌC SINH
    hocsinh_id = fields.Many2one('ekids.hocsinh', string="Họ và tên", required=True)  # [cite: 2]

    name = fields.Char(string="Tên",compute="_compute_name")
    kehoach_linhvuc_ids = fields.One2many("ekids.kehoach_linhvuc",
                                          inverse_name="kehoach_id",
                                          string="Lĩnh vực và độ tuổi thuộc kết luận")


    ketluan_id = fields.Many2one('ekids.kehoach_ketluan', string="Kết luận", required=True)  # [cite: 2]




    trangthai = fields.Selection([
        (kehoach_util.KEHOACH_DANG_LAP, "Đang lập"),
        (kehoach_util.KEHOACH_DANG_PHEDUYET, "Đợi duyệt"),
        (kehoach_util.KEHOACH_DANG_CANTHIEP, "Đang can thiệp"),
        (kehoach_util.KEHOACH_HET_HIEULUC, "Hết hiệu lực"),


    ], string="Trạng thái",default=kehoach_util.KEHOACH_DANG_LAP)

    trangthai_pheduyet = fields.Selection([
        (kehoach_util.PHEDUYET_DOI_DUYET, "Đợi phê duyệt"),
        (kehoach_util.PHEDUYET_CAN_DIEUCHINH, "Cần điều chỉnh"),
        (kehoach_util.PHEDUYET_DA_DUYET, "Đã được duyệt"),


    ], string="Trạng thái phê duyệt", default=kehoach_util.PHEDUYET_DOI_DUYET)

    trangthai_canthiep = fields.Selection([
        (kehoach_util.CANTHIEP_DANG_THUCHIEN, "Đợi phê duyệt"),
        (kehoach_util.CANTHIEP_DOI_DUYET, "Cần điều chỉnh"),

    ], string="Trạng thái phê duyệt Kết quả can thiệp", default=kehoach_util.CANTHIEP_DANG_THUCHIEN)

    tu_ngay = fields.Date(
        string="Từ ngày",
        required=True,
    )

    # Default = Hôm nay + 31 ngày (Dùng hàm lambda để tính toán nhanh)

    den_ngay = fields.Date(
        string="Đến ngày",
        required=True,
    )

    songay = fields.Integer(string="Số ngày", default=31)

    gv_lapkehoach_id = fields.Many2one('ekids.giaovien'
                                       , string="Giáo viên [Lập kế hoạch]"
                                       , compute="_compute_gv_lapkehoach_id"
                                       , store=False)

    gv_kiemduyet_id = fields.Many2one('ekids.giaovien'
                                      , string="Giáo viên [Kiểm duyệt chuyên môn]"
                                      , compute="_compute_gv_kiemduyet_id"
                                      , store=False)

    gv_canthiep_id = fields.Many2one('ekids.giaovien'
                                     , string="Giáo viên [Can thiệp]"
                                     , compute="_compute_gv_canthiep_id"
                                     , store=False)




    kehoach_muctieu_ids = fields.Many2many(comodel_name="ekids.kehoach_muctieu"
                                   , relation="ekids_kehoach_muctieu4kehoach_rel"
                                   , column1="kehoach_id"
                                   , column2="kehoach_muctieu_id"
                                   , string="Các mục tiêu cho kế hoạch")

    desc = fields.Html(string="Ý kiến phê duyệt")

    is_gui_pheduyet = fields.Boolean(compute="_compute_is_gui_pheduyet")
    is_pheduyet = fields.Boolean(compute="_compute_is_pheduyet")
    is_readonly = fields.Boolean(compute="_compute_is_readonly")

    def _compute_is_readonly(self):
        for record in self:
            is_readonly= True
            if (record.trangthai == kehoach_util.KEHOACH_DANG_LAP
                or record.trangthai == kehoach_util.PHEDUYET_CAN_DIEUCHINH):
                is_readonly = False
            record.is_readonly = is_readonly

    @api.depends("tu_ngay")
    def _compute_name(self):
        today =date.today()
        today.month
        for record in self:
            tu_ngay =record.tu_ngay
            name =""
            if tu_ngay:
                name = "Tháng "+ str(tu_ngay.month) +"/" + str(tu_ngay.year)

            record.name = name
    @api.depends("ketluan_id")
    def _compute_gv_lapkehoach_id(self):
        for record in self:
            record.gv_lapkehoach_id =record.ketluan_id.gv_lapkehoach_id

    @api.depends("ketluan_id")
    def _compute_gv_kiemduyet_id(self):
        for record in self:
            record.gv_kiemduyet_id = record.ketluan_id.gv_kiemduyet_id

    @api.depends("ketluan_id")
    def _compute_gv_canthiep_id(self):
        for record in self:
            record.gv_canthiep_id = record.ketluan_id.gv_canthiep_id



    def _compute_is_gui_pheduyet(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for kehoach in self:
            if (kehoach.trangthai== kehoach_util.KEHOACH_DANG_LAP or
                kehoach.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH):
                if (is_admin or kehoach.ketluan_id.gv_lapkehoach_id.user_id.id == user.id):
                    kehoach.is_gui_pheduyet = True
                else:
                    kehoach.is_gui_pheduyet = False
            else:
                kehoach.is_gui_pheduyet= False

    def _compute_is_pheduyet(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for kehoach in self:
            if (kehoach.trangthai == kehoach_util.KEHOACH_DANG_PHEDUYET
                and kehoach.trangthai_pheduyet == kehoach_util.PHEDUYET_DOI_DUYET):
                if (is_admin or  kehoach.ketluan_id.gv_kiemduyet_id.user_id.id == user.id):
                    kehoach.is_pheduyet = True
                else:
                    kehoach.is_pheduyet = False
            else:
                kehoach.is_pheduyet = False




    def _compute_kehoach_linhvuc(self):
        for record in self:
            record.kehoach_linhvuc_ids = record.ketluan_id.kehoach_linhvuc_ids


    def _compute_index(self):
        index = len(self)
        for record in self:
            record.index = index
            index -= 1

    @api.onchange("tu_ngay")
    def _onchage_tu_ngay(self):
        for record in self:
            if record.tu_ngay:
                record.den_ngay = record.tu_ngay + timedelta(days=30)
            else:
                # Nếu người dùng xóa Từ ngày, có thể tự động xóa luôn Đến ngày cho đồng bộ
                record.den_ngay = False


    @api.onchange("den_ngay")
    def _onchage_den_ngay(self):
        for record in self:
            if record.tu_ngay and record.den_ngay:
                # Đóng ngoặc và thêm .days để lấy số nguyên
                record.songay = (record.den_ngay - record.tu_ngay).days + 1
            else:
                # Nếu 1 trong 2 ô ngày bị trống, set số ngày về 0
                record.songay = 0






    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            result = super(KeHoach, self).create(vals)
            if result:
                is_trung = result.func_kiemtra_kehoach_trung_thoigian()
                if is_trung:
                    raise UserError(
                        "Kế hoạch của Học sinh [" + result.hocsinh_id.name + "] Được lập trong khoản thời gian trên đang bị trùng với thời gian của kế hoạch khác !")

                # Tinh toan so ca trong
                result.func_tao_macdinh_kehoach_muctieu()
                records.append(result)
        return records[0] if len(records) == 1 else records

    @api.model
    def write(self, vals):
        result = super().write(vals)
        if result:
            is_trung = self.func_kiemtra_kehoach_trung_thoigian()
            if is_trung:
                raise UserError("Kế hoạch của Học sinh [" + result.hocsinh_id.name +"] Được lập trong khoản thời gian trên đang bị trùng với thời gian của kế hoạch khác !")
            if "kehoach_linhvuc_ids" in vals:
                self.func_tao_macdinh_kehoach_muctieu()
        return result

    def func_kiemtra_kehoach_trung_thoigian(self):
        self.ensure_one()

        # Chốt chặn an toàn: Nếu chưa điền đủ ngày thì không kiểm tra để tránh lỗi
        if not self.tu_ngay or not self.den_ngay:
            return False

        # 1. Khởi tạo Domain lọc các kế hoạch có khoảng thời gian giao nhau
        domain = [
            ('tu_ngay', '<=', fields.Date.to_date(self.den_ngay)),
            ('den_ngay', '>=', fields.Date.to_date(self.tu_ngay)),
        ]

        # 2. Định hướng nghiệp vụ bổ sung (Tùy chọn gom cụm dữ liệu):
        # Thông thường sẽ chỉ xét trùng lịch trên cùng 1 Học sinh hoặc cùng 1 Cơ sở.
        # Nếu anh muốn xét trùng lịch của riêng học sinh đó, hãy mở comment dòng dưới:
        if self.hocsinh_id:
            domain.append(('hocsinh_id', '=', self.hocsinh_id.id))

        # 3. CHỐT CHẶN CHÍ MẠNG: Nếu là kế hoạch đã có ID (hành động sửa/ghi lại)
        # thì phải loại trừ chính bản ghi hiện tại ra khỏi danh sách tìm kiếm, tránh tự trùng với chính mình.
        if self.id:
            domain.append(('id', '!=', self.id))

        # 4. Sử dụng search_count để đếm số bản ghi trùng lặp (Tối ưu hiệu năng, không tốn RAM load dữ liệu)
        trung_lich_count = self.env['ekids.kehoach'].search_count(domain)

        # Trả về True nếu số lượng > 0 (Có trùng), ngược lại trả về False
        return trung_lich_count > 0


    def func_tao_macdinh_kehoach_muctieu(self):
        # unlink cái cũ
        kh_muctieus = self.func_danhsach_kehoach_muctieu(self.id)
        if kh_muctieus:
            for kh_muctieu in kh_muctieus:
                kh_muctieu.unlink()
        # tao cai moi
        if self.kehoach_linhvuc_ids:
            for lv in self.kehoach_linhvuc_ids:
                muctieus = self.func_danhsach_muctieu(lv.linhvuc_id.id,lv.tuoi_id.id)
                if muctieus:
                    for muctieu in muctieus:
                        data={
                            'kehoach_id':self.id,
                            'muctieu_id':muctieu.id
                        }
                        self.env['ekids.kehoach_muctieu'].create(data)

    def func_danhsach_kehoach_muctieu(self, kehoach_id):
        domain = [('kehoach_id', '=', kehoach_id)]
        muctieus = self.env['ekids.kehoach_muctieu'].search(domain)
        return muctieus
    def func_danhsach_muctieu(self,linhvuc_id,tuoi_id):
        domain =[('linhvuc_id','=',linhvuc_id)]
        if tuoi_id:
            domain.append(('tuoi_id', '=', tuoi_id))
        muctieus = self.env['ekids.ct_muctieu'].search(domain)
        return muctieus

    def action_xem_ketluan(self):
        kehoach = self.env['ekids.kehoach'].browse(self.id)
        if kehoach:

            form_view_id = self.env.ref('ekids_canthiep.kehoach_ketluan_form').id
            return {
                'type': 'ir.actions.act_window',
                'name': 'XEM KẾT LUẬN',
                'res_model': 'ekids.kehoach_ketluan',
                'view_mode': 'form',
                'res_id':kehoach.ketluan_id.id,
                'views': [(form_view_id, 'form')],
                'target': 'new',
                'domain': [('coso_id', '=', kehoach.coso_id.id)],
                'context': {
                    'default_coso_id': kehoach.coso_id.id,
                    'default_hocsinh_id': kehoach.hocsinh_id.id,
                    # 🌟 THÊM 3 DÒNG CHỐT CHẶN DƯỚI ĐÂY ĐỂ KHÓA ĐỂN FORM VIEW
                    'edit': False,  # 🚫 Tắt hoàn toàn tính năng và ẩn nút [Sửa]
                    'create': False,  # 🚫 Tắt tính năng và ẩn nút [Tạo mới]
                    'delete': False,  # 🚫 Tắt tính năng và ẩn nút [Xóa]

                },
            }





    def action_gui_pheduyet(self):
        if (self.trangthai == kehoach_util.KEHOACH_DANG_LAP
                or self.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH):

            self.trangthai = kehoach_util.KEHOACH_DANG_PHEDUYET
            self.trangthai_pheduyet = kehoach_util.PHEDUYET_DOI_DUYET

    def action_pheduyet_dat(self):
        if self.trangthai == kehoach_util.KEHOACH_DANG_PHEDUYET:
            self.trangthai_pheduyet = kehoach_util.PHEDUYET_DA_DUYET
            self.trangthai = kehoach_util.KEHOACH_DANG_CANTHIEP



    def action_pheduyet_khongdat(self):
        if self.trangthai == kehoach_util.KEHOACH_DANG_PHEDUYET:
            self.trangthai_pheduyet = kehoach_util.PHEDUYET_CAN_DIEUCHINH

    def action_xem_kehoachs(self):

        list_view_id = self.env.ref('ekids_canthiep.kehoach_hocsinh_inherit_list').id
        hocsinh_ids = kehoach_util.func_get_ids_hocsinh_theo_vaitro(self)
        domain =[('coso_id', '=', self.coso_id.id)]
        if hocsinh_ids:
            domain = [('coso_id', '=', self.coso_id.id),('id','in',hocsinh_ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.coso_id.id,
                'search_default_trangthai': '1',
            },
        }

    def action_gui_duyet_ketqua_kehoach(self):
        self.ensure_one()
        if self.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
            kehoach = self.env['ekids.kehoach'].browse(self.id)
            if kehoach:
                kehoach._write({"trangthai_canthiep":kehoach_util.CANTHIEP_DOI_DUYET})


        list_view_id = self.env.ref('ekids_canthiep.kehoach_hocsinh_inherit_list').id
        hocsinh_ids = kehoach_util.func_get_ids_hocsinh_theo_vaitro(self)
        domain =[('coso_id', '=', self.coso_id.id)]
        if hocsinh_ids:
            domain = [('coso_id', '=', self.coso_id.id),('id','in',hocsinh_ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.coso_id.id,
                'search_default_trangthai': '1',
            },
        }



    def action_xem_kehoach(self):
        form_view_id = self.env.ref('ekids_canthiep.kehoach_form').id

        return {
            'type': 'ir.actions.act_window',
            'name': 'LẬP KẾ HOẠCH',
            'res_model': 'ekids.kehoach',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(form_view_id, 'form')],
            'target': 'current',
            'domain': [('coso_id', '=', self.coso_id.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.hocsinh_id.id
            },
        }

    def action_canthiep(self):
        return False

    def action_ketthuc_kehoach(self):
        return None







