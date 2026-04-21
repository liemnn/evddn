from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError

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



class GiaoVien(models.Model):
    _name = "ekids.giaovien"
    _description = "Đối tượng giáo viên của cơ sở"
    _order = "dilam_tungay asc ,create_date asc,id asc"


    sequence = fields.Integer(string="TT", compute="_compute_sequence")
    coso_id = fields.Many2one("ekids.coso", string="Thuộc cơ sở",required=True, ondelete="restrict")

    name = fields.Char(string="Họ và tên", required=True)

    ten = fields.Char(string="ten", compute="_compute_ten", store=True)
    cccd = fields.Char(string="CCCD",required=True)
    avatar = fields.Binary(string="Ảnh đại diện")
    dienthoai = fields.Char(string="Điện thoại(sử dụng làm tài khoản)",required=True)
    gioitinh  = fields.Selection([("0","Nữ"),("1","Nam")],'Giới tính',required=True)
    ngaysinh = fields.Date(string="Ngày sinh",required=True)

    desc = fields.Html(string="Kinh nghiệm làm việc/thông tin giáo viên")


    diachi_quequan = fields.Char(string="Quê quán")
    diachi_cutru = fields.Char(string="Địa chỉ đang cư trú")
    trinhdo = fields.Selection([("0", "Trung cấp")
                                   , ("1", "Cao đẳng")
                                   , ("2", "Đại học")
                                   , ("3", "Thạc sỹ")
                                   , ("4", "Tiến sỹ")
                                ], string="Trình độ")
    chuyennganh = fields.Selection([("0", "Mầm non")
                                   , ("1", "Tâm lý")
                                   , ("2", "Giáo dục đặc biệt")
                                   , ("3", "Khác")

                                ], string="Chuyên ngành")

    tinhtrang_honnhan = fields.Selection([("1", "Đã có gia đình")
                                             , ("0", "Chưa có gia đình")
                                             , ("1", "Khác")
                                          ]
                                         ,'Tình trạng hôn nhân',required=True)

    dilam_tungay = fields.Date(string="*Ngày đi làm",required=True)
    dilam_denngay = fields.Date(string="Ngày nghỉ làm")
    tham_nien = fields.Float(string="Thâm niên", digits=(10, 1),compute="_compute_tham_nien")

    so_hopdong_laodong= fields.Char(string="Số hợp đồng lao động")
    trangthai = fields.Selection([
        ("1","Đang làm việc"),
        ("0","Đã nghỉ làm"),
        ("2", "Tạm nghỉ hưởng BHXH (Ốm, Đẻ...")
    ],string="Trạng thái",default="1",required=True)

    is_ngaydilam_rieng = fields.Boolean(string="Thiết lập ngay đi làm đặc thù [Một số ngày trong tuần nghỉ]",
                                        default=False)

    hd_t2 = fields.Boolean(string="T2")
    hd_t3 = fields.Boolean(string="T3")
    hd_t4 = fields.Boolean(string="T4")
    hd_t5 = fields.Boolean(string="T5")
    hd_t6 = fields.Boolean(string="T6")
    hd_t7 = fields.Boolean(string="T7")
    hd_t8 = fields.Boolean(string="CN")


    user_id = fields.Many2one("res.users",string="Tài khoản")

    group_ids =fields.One2many("res.groups",string="Quyền truy cập",inverse_name="id")

    nguoithan_ids = fields.One2many("ekids.giaovien_nguoithan","giaovien_id", string="Thông tin người thân")
    hoctapcongtac_ids = fields.One2many("ekids.giaovien_hoctapcongtac", "giaovien_id", string="Quá trình học tập/công tác")
    khenthuong_ids = fields.One2many("ekids.giaovien_khenthuong", "giaovien_id",
                                        string="Khen thưởng/Kỷ luật")


    nghiphep_ids = fields.One2many("ekids.giaovien_nghiphep", "giaovien_id",
                                        string="Nghỉ phép")

    dm_chitra_ids = fields.Many2many(comodel_name="ekids.luong_dm_chitra"
                                    , relation="ekids_giaovien2luong_dm_chitra_rel"
                                    , column1="giaovien_id"
                                    , column2="dm_chitra_id"
                                    , string="Cấu tru lương của giáo viên")

    luong_ids = fields.One2many("ekids.luong", "giaovien_id",
                                        string="Lương hàng tháng")

    is_taikhoan =fields.Boolean(string="Đã có tài khoản",compute="_compute_is_taikhoan")

    phep_duocphep = fields.Integer(string="Số ngày được [nghỉ phép] trong năm nay")
    phep_da_sudung = fields.Integer(string="Ngày phép đã sử dụng",compute="_compute_phep_da_sudung",store=True)
    phep_con_trongnam = fields.Integer(string="Ngày phép con lại trong năm",store=True)

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'ekids_giaovien_giayto2ir_attachments_rel',
        'giaovien_id',
        'attachment_id',
        string="Hồ sơ/giấy tờ"
    )
    is_hoanthien_hoso = fields.Boolean(string="Hồ sơ", default=False)


    _sql_constraints = [
        ('ekids_giaovien_unique_user_id', 'unique(user_id)', 'Giáo viên chỉ có một tài khoản !')
    ]

    def _compute_sequence(self):
        index =1
        for record in self:
            record.sequence = index
            index +=1

    @api.depends('dilam_tungay','hoctapcongtac_ids')
    def _compute_tham_nien(self):
        for record in self:
            thamnien =giaovien_util.func_get_thamnien(record)
            htcts= record.hoctapcongtac_ids
            if htcts:
                for htct in htcts:
                    if htct.is_tham_nien_duoccong == True:
                        thamnien+= htct.tham_nien
            record.tham_nien =thamnien
    @api.depends('name')
    def _compute_ten(self):
        for record in self:
            if record.name:
                last_word = record.name.strip().split()[-1]
                record.ten = last_word
            else:
                record.ten = ""

    @api.depends('phep_duocphep','nghiphep_ids')
    def _compute_phep_da_sudung(self):
        day =date.today()
        tu_ngay = date(day.year,1,1)
        den_ngay = date(day.year, 12, 31)
        nghiles = nghile_util.func_get_nghiles_trong_khoang_thoigian(self, self.coso_id,None, tu_ngay, den_ngay)

        for record in self:
            nghipheps = giaovien_util.func_get_nghipheps_trong_khoang_thoigian(self,record.coso_id, record, nghiles, None,tu_ngay, den_ngay)

            if nghipheps:
                record.phep_da_sudung = len(nghipheps)
                record.phep_con_trongnam = record.phep_duocphep - record.phep_da_sudung
            else:
                record.phep_da_sudung=0
                record.phep_con_trongnam = record.phep_duocphep - record.phep_da_sudung




    def _compute_is_taikhoan(self):
        for record in self:
            if record.user_id:
               record.is_taikhoan = True
            else:
                record.is_taikhoan = False





    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            coso = None

            # Ưu tiên lấy từ context nếu có
            coso_id = self.env.context.get('default_coso_id') or vals.get('coso_id')
            if coso_id:
                vals['coso_id'] = coso_id  # đảm bảo có trong vals luôn
            records.append(super(GiaoVien, self).create(vals))
        return records[0] if len(records) == 1 else records


    # Bổ sung group by du trạng thái không có và hiển thị list có phân loại theo trạng thái


    def action_mo_popup_taikhoan_giaovien(self):
        self.ensure_one()
        sdt = self.dienthoai
        user = self.user_id
        if not sdt or sdt == '':
            raise ValidationError(
                _("Bạn cần nhập số điện thoại của giáo viên để tạo tài khoản !"))

        #TH1 kiểm tra tài khoản này đã có ai sử dụng chưa nếu chưa có gán cho cán bộ này
        if (sdt and not user):
            user = self.env['res.users'].search([('login', '=', sdt)], limit=1)
            if user:
                count= self.env['ekids.giaovien'].search_count([('user_id', '=', user.id)])
                if count <=0:
                    self.user_id = user.id
                    user = self.user_id
                else:
                    raise ValidationError(
                        _("Tài khoản [Số điện thoại] đã có người khác sử dụng!"))

        view_id = self.env.ref('ekids_giaovien.view_ekids_giaovien_user_form').id
        coso_ids =self.env['ekids.coso'].search([]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Thông tin tài khoản'),
            'res_model': 'res.users',
            'view_mode': 'form',
            'views': [(view_id,'form')],
            'res_id':user.id,
            'target': 'new',
            'context':{
                'default_name':self.name,
                'default_login': self.dienthoai,
                'default_coso_ids':coso_ids,
                'default_giaovien_id': self.id,


            },
        }


    def action_xoa_taikhoan_giaovien(self):
        user = self.user_id
        if user:
            # nếu tài khoản không phải la tài khoản cấp cho cơ sở riêng tài khoản này không cho thay đổi
            coso = self.coso_id
            if coso.user_id.id != self.user_id.id:
                self.user_id =False
                self.is_taikhoan = False
                user.unlink()
            else:
                raise ValidationError(
                    _("Tài khoản này là tài khoản Quản trị/ Quản lý cơ sở được cấp khi thuê bạn không thể xóa !"))










