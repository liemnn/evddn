from odoo import models, fields, api
from datetime import  timedelta,date
import uuid

from odoo.exceptions import UserError, AccessError

from .ekids_kehoach_copy_abstractmodel import KeHoachCopyAbstractModel



import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
    from odoo.addons.ekids_func import giaovien_util

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

    kehoach_truoc_id = fields.Many2one(
        'ekids.kehoach',
        string='Kế hoạch trước nó',
    )


    trangthai = fields.Selection([
        (kehoach_util.KEHOACH_DANG_LAP, "Đang lập"),
        (kehoach_util.KEHOACH_DANG_PHEDUYET, "Đang kiểm duyệt"),
        (kehoach_util.KEHOACH_DANG_CANTHIEP, "Đang can thiệp"),
        (kehoach_util.KEHOACH_HET_HIEULUC, "Hết hiệu lực"),


    ], string="Trạng thái",default=kehoach_util.KEHOACH_DANG_LAP)



    trangthai_pheduyet = fields.Selection([
        (kehoach_util.PHEDUYET_DOI_DUYET, "Đợi phê duyệt"),
        (kehoach_util.PHEDUYET_CAN_DIEUCHINH, "Cần điều chỉnh"),
        (kehoach_util.PHEDUYET_DA_DUYET, "Đã được duyệt"),


    ], string="Trạng thái phê duyệt", default=kehoach_util.PHEDUYET_DOI_DUYET)


    tu_ngay = fields.Date(
        string="Từ ngày",
        required=True,
    )

    # Default = Hôm nay + 31 ngày (Dùng hàm lambda để tính toán nhanh)

    den_ngay = fields.Date(string="Đến ngày",
        required=True,
    )

    songay = fields.Integer(string="Số ngày", default=31)


    ngay_guiduyet = fields.Datetime(string="Ngày [Gửi duyệt]")
    ngay_duyet = fields.Datetime(string="Ngày [Duyệt]")
    ngay_ketthuc = fields.Datetime(string="Ngày [Kết thúc]")



    gv_kiemduyet_id = fields.Many2one('ekids.giaovien'
                                      , string="Giáo viên [Kiểm duyệt chuyên môn]"
                                      , compute="_compute_gv_kiemduyet_id"
                                      , store=False)

   # Đổi sang Many2many để nhận diện đúng tập hợp nhiều giáo viên
    gv_canthiep_ids = fields.Many2many(
        'ekids.giaovien',
        string="Giáo viên [Can thiệp]",
        compute="_compute_gv_canthiep_ids",
        store=False  # Không lưu trữ dưới DB, tính toán động theo Kết luận
    )

    gv_lapkehoach_id = fields.Many2one('ekids.giaovien'
                                      , string="Giáo viên [Lập kế hoạch/Can thiệp]", required=True)

    desc = fields.Html(string="Ý kiến phê duyệt")

    is_gui_pheduyet = fields.Boolean(compute="_compute_is_gui_pheduyet")
    is_pheduyet = fields.Boolean(compute="_compute_is_pheduyet")
    is_kiemduyet = fields.Boolean(compute="_compute_is_kiemduyet")
    is_readonly = fields.Boolean(compute="_compute_is_readonly")
    is_header_open = fields.Boolean(compute="_compute_is_header_open")
    is_show_wiget_canthiep = fields.Boolean(compute="_compute_is_show_wiget_canthiep")
    is_xoa = fields.Boolean(compute="_compute_is_xoa")

    access_token = fields.Char(string="Thẻ truy cập nhanh", readonly=True, copy=False)
    share_full_url = fields.Char("Chia sẻ full", compute="_compute_urls")
    share_short_url = fields.Char("Chia sẻ short", compute="_compute_urls")

    @api.depends('access_token')
    def _compute_urls(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for rec in self:
            token = rec.access_token or str(uuid.uuid4())  # Fallback an toàn
            rec.share_short_url = f"{base_url}/kehoach/0/{token}"
            rec.share_full_url = f"{base_url}/kehoach/1/{token}"

    def _compute_is_xoa(self):
        for record in self:
            is_xoa = False
            if self.env.user._is_admin():
                is_xoa = True
            else:
                if (self.trangthai == kehoach_util.KEHOACH_DANG_LAP
                        or self.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH):
                    is_xoa = True

            record.is_xoa = is_xoa
    def _compute_is_show_wiget_canthiep(self):
        for record in self:
            is_show_wiget_canthiep = False
            if (record.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP
                or record.trangthai == kehoach_util.KEHOACH_HET_HIEULUC):
                is_show_wiget_canthiep =True
            record.is_show_wiget_canthiep = is_show_wiget_canthiep

    def _compute_is_header_open(self):
        for record in self:
            is_header_open = False
            if (record.trangthai == kehoach_util.KEHOACH_DANG_LAP
                    or record.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH):
                is_header_open = True
            record.is_header_open = is_header_open

    def _compute_is_readonly(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        for record in self:
            if not record.access_token:
                record.access_token=str(uuid.uuid4())

            is_readonly= True
            if is_admin:
                is_readonly = False
            else:
                if (record.trangthai == kehoach_util.KEHOACH_DANG_LAP
                    or record.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH):
                    giaoviens = self.ketluan_id.gv_canthiep_ids
                    user_ids = giaoviens.mapped('user_id').ids
                    if user.id in user_ids:
                        is_readonly = False
                else:
                    if (record.trangthai == kehoach_util.KEHOACH_DANG_PHEDUYET
                        and record.trangthai_pheduyet == kehoach_util.PHEDUYET_DOI_DUYET):
                        giaovien = self.ketluan_id.gv_kiemduyet_id
                        if giaovien.user_id.id == user.id:
                            is_readonly= False


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
    def _compute_gv_kiemduyet_id(self):
        for record in self:
            record.gv_kiemduyet_id = record.ketluan_id.gv_kiemduyet_id

    @api.depends('ketluan_id', 'ketluan_id.gv_canthiep_ids')
    def _compute_gv_canthiep_ids(self):
        for rec in self:
            # Nếu có kết luận con và kết luận đó đã chọn giáo viên can thiệp
            if rec.ketluan_id and rec.ketluan_id.gv_canthiep_ids:
                # Gán thẳng recordset Many2many từ kết luận sang kế hoạch
                rec.gv_canthiep_ids = rec.ketluan_id.gv_canthiep_ids
            else:
                # Nếu không có, gán tập hợp rỗng bằng cách lệnh [(5, 0, 0)] hoặc lệnh clear của Odoo
                rec.gv_canthiep_ids = [(5, 0, 0)]


    def _compute_is_gui_pheduyet(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for kehoach in self:
            if (kehoach.trangthai== kehoach_util.KEHOACH_DANG_LAP or
                kehoach.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH):
                giaoviens =kehoach.ketluan_id.gv_canthiep_ids
                user_ids = giaoviens.mapped('user_id').ids
                if (is_admin or user.id in user_ids):
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

    def _compute_is_kiemduyet(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for kehoach in self:
            if kehoach.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
                if (is_admin or  kehoach.ketluan_id.gv_kiemduyet_id.user_id.id == user.id):
                    kehoach.is_kiemduyet = True
                else:
                    kehoach.is_kiemduyet = False
            else:
                kehoach.is_kiemduyet = False




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
    def func_kiemtra_kehoach_trung_thoigian(self):

        self.ensure_one()

        # Chốt chặn an toàn: Nếu chưa điền đủ ngày thì không kiểm tra để tránh lỗi
        if not self.tu_ngay or not self.den_ngay:
            return False

        giaovien = self.gv_lapkehoach_id
        if not self.gv_lapkehoach_id:
            giaovien = giaovien_util.func_get_giaovien_tu_user(self)

        # 1. Khởi tạo Domain lọc các kế hoạch có khoảng thời gian giao nhau
        domain = [
            ('tu_ngay', '<=', fields.Date.to_date(self.den_ngay)),
            ('den_ngay', '>=', fields.Date.to_date(self.tu_ngay)),
        ]

        if giaovien:
            domain.append(('gv_lapkehoach_id', '=', giaovien.id))

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
        for rec in self:
            if (rec.trangthai == kehoach_util.KEHOACH_DANG_LAP
                    or rec.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH):
                data ={
                    'trangthai': kehoach_util.KEHOACH_DANG_PHEDUYET,
                    'trangthai_pheduyet': kehoach_util.PHEDUYET_DOI_DUYET,
                    'ngay_guiduyet': fields.Date.today(),
                }
                rec.write(data)

    def action_pheduyet_dat(self):
        for rec in self:
            if rec.trangthai == kehoach_util.KEHOACH_DANG_PHEDUYET:
                data={
                    'trangthai_pheduyet': kehoach_util.PHEDUYET_DA_DUYET,
                    'trangthai': kehoach_util.KEHOACH_DANG_CANTHIEP,
                }
                rec.write(data)







    def action_pheduyet_khongdat(self):
        if self.trangthai == kehoach_util.KEHOACH_DANG_PHEDUYET:
            self.trangthai_pheduyet = kehoach_util.PHEDUYET_CAN_DIEUCHINH
    def action_xoa(self):
        coso =self.coso_id
        if self.env.user._is_admin():
            self.unlink()
        else:
            if (self.trangthai == kehoach_util.KEHOACH_DANG_LAP
                or self.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH):
                self.unlink()
            else:
                raise UserError ("Kế hoạch đang ở trạng thái không cho phép xóa")

        if coso:
            url = coso.action_danhsach_hocsinh_lap_kehoach()
            if url:
                return url




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
                kehoach._write({"trangthai":kehoach_util.KEHOACH_HET_HIEULUC})


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

        return {
            'type': 'ir.actions.act_window',
            'name': 'LẬP KẾ HOẠCH',
            'res_model': 'ekids.kehoach',
            'view_mode': 'form',
            'res_id': self.id,

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
        if self.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
            is_chophep_ketthuc =False
            user = self.env.user
            is_admin = user.has_group('base.group_system')
            if is_admin:
                is_chophep_ketthuc =True
            else:
                giaovien = self.ketluan_id.gv_kiemduyet_id
                # Phòng thủ kiểm tra chắc chắn để tránh lỗi sập hệ thống (Null Pointer) khi chưa chọn giáo viên
                if giaovien and giaovien.user_id and giaovien.user_id.id == user.id:
                   is_chophep_ketthuc = True
        if is_chophep_ketthuc:
            self.trangthai = kehoach_util.KEHOACH_HET_HIEULUC


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
            if ('tu_ngay' in vals
                or 'den_ngay' in vals):
                # nếu có thay đôi về ngày tháng cần kiểm tra trùng
                is_trung = self.func_kiemtra_kehoach_trung_thoigian()
                if is_trung:
                    raise UserError("Thời gian của [Kế hoạch] đang trùng với kế hoạch khác")

            if "kehoach_linhvuc_ids" in vals:
                self.func_tao_macdinh_kehoach_muctieu()
        return result




    # 🌟 BỎ HOÀN TOÀN decorator @api.model ở đây
    def unlink(self):
        # 1. Nếu là Admin tối cao thì cho qua luôn, không cần duyệt qua vòng lặp
        if self.env.user._is_admin():
            return super(KeHoach, self).unlink()

        # 2. Duyệt qua từng bản ghi được chọn xóa để kiểm tra điều kiện trạng thái
        for rec in self:
            # Kiểm tra nếu thỏa mãn điều kiện Đang lập HOẶC Cần điều chỉnh thì cho phép qua, ngược lại chặn đứng
            if not (rec.trangthai == kehoach_util.KEHOACH_DANG_LAP or
                    rec.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH):
                raise UserError(f"Kế hoạch [{rec.name or ''}] đang ở trạng thái không cho phép xóa!")

        # 3. Gọi hàm super() duy nhất một lần cuối cùng để thực thi xóa dưới DB
        return super(KeHoach, self).unlink()














