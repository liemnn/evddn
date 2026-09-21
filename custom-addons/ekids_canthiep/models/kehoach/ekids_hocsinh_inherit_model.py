from odoo import models, fields, api, exceptions
from datetime import  timedelta,date,datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import uuid


from .ekids_hocsinh_kehoach_action_abstractmodel import HocSinhKeHoachActionAbstractModel
from .ekids_hocsinh_kehoach_abstractmodel import HocSinhKeHoachAbstractModel
from .ekids_hocsinh_kehoach_hoso_abstractmodel import HocSinhKeHoachHoSoAbstractModel
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



class HocSinhInherit(models.Model
    ,HocSinhKeHoachAbstractModel
    ,HocSinhKeHoachActionAbstractModel
    ,HocSinhKeHoachHoSoAbstractModel):

    _inherit = "ekids.hocsinh"

    trangthai_ketluan = fields.Selection([
        (kehoach_util.KETLUAN_CHUA_CO, "Chưa có"),
        (kehoach_util.KETLUAN_DANG_TAO, "Đang soạn thảo"),
        (kehoach_util.KETLUAN_CHOPHEP_LAP_KEHOACH, "Cho phép lập [Kế hoạch]"),
        (kehoach_util.KETLUAN_HET_HIEULUC, "Hết hiệu lực lập [Kế hoạch]"),

    ],compute="_compute_trangthai_ketluan"
    ,string="Trạng thái")

    trangthai_kehoach = fields.Selection([
        (kehoach_util.HOCSINH_CHUA_CO_KEHOACH, "Chưa có"),
        (kehoach_util.HOCSINH_DANG_LAP_KEHOACH, "Đang lập"),
        (kehoach_util.HOCSINH_DANG_CANTHIEP, "Đang can thiệp"),
        (kehoach_util.HOCSINH_HET_HIEULUC, "Hết hiệu lực"),
        (kehoach_util.HOCSINH_DA_DUYET, "Đã duyệt"),
        (kehoach_util.HOCSINH_DOI_DUYET, "Đợi duyệt"),
        (kehoach_util.HOCSINH_CAN_DIEUCHINH, "Cần chỉnh sửa"),


    ],string="Trạng thái kế hoạch",compute="_compute_trangthai_kehoach")







    kehoach_ids = fields.One2many("ekids.kehoach",
             "hocsinh_id", string="Các kế hoạch can thệp của học sinh")

    ketluan_ids = fields.One2many("ekids.kehoach_ketluan",
                                  "hocsinh_id", string="Kết luận")


    is_tao_ketluan = fields.Boolean(compute="_compute_is_tao_ketluan",compute_sudo=False)
    is_sua_ketluan = fields.Boolean(compute="_compute_is_sua_ketluan", compute_sudo=False)
    is_lap_kehoach = fields.Boolean(compute="_compute_is_lap_kehoach",compute_sudo=False)
    is_sua_kehoach = fields.Boolean(compute="_compute_is_sua_kehoach",compute_sudo=False)
    is_kiemduyet = fields.Boolean(compute="_compute_is_kiemduyet",compute_sudo=False)
    is_canthiep = fields.Boolean(compute="_compute_is_canthiep",compute_sudo=False)

    tong_ketluan = fields.Integer(compute="_compute_tong_ketluan", string="Số lượng")
    tong_kehoach = fields.Integer(compute="_compute_tong_kehoach",string="Số lượng")

    tong_kehoach_doiduyet = fields.Integer(compute="_compute_tong_kehoach_doiduyet", string="Số lượng đợi duyệt")
    ngay_guiduyet = fields.Char(string="Ngày [Gửi duyệt]",compute="_compute_tong_kehoach_doiduyet")
    ten_kehoach = fields.Char(string="Kế hoạch tháng", compute="_compute_ten_kehoach")

    ngay_duyet = fields.Char(string="Ngày [Duyệt]", compute="_compute_tong_kehoach_doiduyet")


    tong_kehoach_taomoi = fields.Integer(compute="_compute_tong_kehoach_taomoi", string="Số lượng đã tạo")
    tong_kehoach_dang_canthiep = fields.Integer(compute="_compute_tong_kehoach_dang_canthiep", string="Số lượng đang can thiêp")
    tong_kehoach_da_canthiep = fields.Integer(compute="_compute_tong_kehoach_da_canthiep",string="Số [Kế hoạch] Đã can thiệp")

    ngay_conlai_kehoach = fields.Integer(compute="_compute_ngay_conlai_kehoach",string="Ngày còn lại [Kế hoạch]")

    kehoach_thangnay = fields.Char(compute="_compute_kehoach_thang", string="Có kế hoạch tháng này")
    kehoach_thangtruoc = fields.Char(compute="_compute_kehoach_thang", string="Có kế hoạch tháng trước")
    kehoach_thangsau = fields.Char(compute="_compute_kehoach_thang", string="Có kế hoạch tháng sau")

      # Khai báo trường với default uuid chuẩn
    access_token = fields.Char(
        string="Thẻ truy cập nhanh",
        readonly=True,
        copy=False,
        default=lambda self: str(uuid.uuid4())
    )

    hare_url = fields.Char("Chia sẻ Hồ sơ", compute="_compute_urls")

    @api.depends('access_token')
    def _compute_urls(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for rec in self:
            token = rec.access_token or str(uuid.uuid4())  # Fallback an toàn
            rec.share_url = f"{base_url}/hocsinh/hosocanthiep/{token}"









