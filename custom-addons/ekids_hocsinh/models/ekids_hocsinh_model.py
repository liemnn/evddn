from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _  # <-- THÊM DÒNG NÀY
from .ekids_read_group_abstractmodel import ReadGroupAbstractModel
from datetime import datetime,date
class HocSinh(models.Model,ReadGroupAbstractModel):
    _name = "ekids.hocsinh"
    _description = "Đối tượng học sinh của cơ sở"
    _order = "ngay_nhaphoc asc ,create_date asc,id asc"


    sequence = fields.Integer(string="TT", compute="_compute_sequence")
    ma =fields.Char(string="Mã")
    name = fields.Char(string="*Họ và tên",required=True,index=True)

    ten = fields.Char(string="ten", compute="_compute_ten",store=True,index=True)
    bietdanh = fields.Char(string="Tên gọi ở nhà (Biệt danh)")
    cccd = fields.Char(string="Số định danh cá nhân(nếu có)")
    avatar = fields.Binary(string="Ảnh đại diện")
    ngaysinh = fields.Date(string="*Ngày sinh",required=True)
    tuoi = fields.Char(string="Tuổi", compute="_compute_hocsinh_tuoi",store=True)
    gioitinh  = fields.Selection([("0","Nữ"),("1","Nam")],string="*Giới tính",required=True)
    chieucao = fields.Integer(string="Chiều cao(cm)")
    cannang = fields.Integer(string="Cân nặng(kg)")


    lichsu_mangthai = fields.Html(string="Lịch sử mang thai của mẹ")
    tiensu_giadinh = fields.Html(string="Tiền sử gia đình")
    lichsu_canthiep = fields.Html(string="Lịch sử can thiệp trước đây (nếu có)")
    desc = fields.Html(string="Đặc điểm cần chú ý về trẻ")


    ngay_nhaphoc = fields.Date(string="*Ngày bắt đầu(đi học, đánh giá..)",required=True)
    ngay_nghihoc = fields.Date(string="Ngày nghỉ học")

    dm_chinhsach_giam_id = fields.Many2one("ekids.hocphi_dm_chinhsach_giam",
                                           string="Học sinh thuộc chính sách giảm học phí (nếu có)")

    trangthai = fields.Selection([
            ("1", "Đang theo học"),
            ("2","Đợi đánh giá"),
            ("3", "Đã nghỉ"),
            ("4","Đã đannh giá nhưng không học")
           ]
        ,string="Trạng thái học sinh theo học",default="1",required=True)

    is_ngaydihoc_rieng = fields.Boolean(string="Thiết lập ngay đi học Riêng [Một số ngày trong tuần nghỉ]", default=False)

    hd_t2 = fields.Boolean(string="T2")
    hd_t3 = fields.Boolean(string="T3")
    hd_t4 = fields.Boolean(string="T4")
    hd_t5 = fields.Boolean(string="T5")
    hd_t6 = fields.Boolean(string="T6")
    hd_t7 = fields.Boolean(string="T7")
    hd_t8 = fields.Boolean(string="CN")


    user_id = fields.Many2one("res.users",string="Tài khoản")
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True,ondelete="restrict")
    #số tiền trong ví điện tử nộp của phụ huynh cho hoc sinh
    tien = fields.Float(string='Số tiền(vnđ)'
                        , digits=(10, 0), default=0)

    is_dong_hocphi_theoky = fields.Boolean(compute="_compute_is_dong_hocphi_theoky")

    def _compute_is_dong_hocphi_theoky(self):
        for record in self:
            if record.coso_id.is_dong_hocphi_theoky == True:
                record.is_dong_hocphi_theoky = True
            else:
                record.is_dong_hocphi_theoky = False

    @api.constrains('trangthai', 'ngaynghi')
    def _check_ngaynghi_required(self):
        for rec in self:
            if rec.trangthai == '3' and not rec.ngay_nghihoc:
                raise ValidationError("Học sinh [Nghỉ học bắt buộc phải nhập [ngày nghỉ học] cho học sinh đó !")


    def _compute_sequence(self):
        index =1
        for record in self:
            record.sequence = index
            index +=1

    #thong tin phụ huynh



    giadinh = fields.Selection([("0", "Thu nhập Dưới trung bình")
                                           ,("1", "Thu nhập Trung bình")
                                           ,("2", "Thu nhập Trung bình cao")
                                           ,("3", "Thu nhập Cao")
                                            ],"Tình trạng kinh tế gia đình")

    dm_tinh_id = fields.Many2one("ekids.dm_tinh",
                                 string="Tỉnh")
    dm_xa_id = fields.Many2one("ekids.dm_xa", string="Phường/Xã", domain="[('dm_tinh_id','=',ph_dm_tinh_id)]")
    diachi_chitiet = fields.Char(string="Số nhà/ đường phố, thôn xóm")


    ketluan_ids = fields.One2many("ekids.ketluan", "hocsinh_id"
                                        , string="Kết luận đánh giá")



    thu_bantru_ids = fields.Many2many(comodel_name="ekids.hocphi_dm_thu_bantru"
                                     , relation="ekids_hocsinh2dm_thu_bantru_rel"
                                     , column1="hocsinh_id"
                                     , column2="dm_thu_bantru_id"
                                     , string="Khoản thu bán trú của học sinh")

    ca_canthiep_ids = fields.One2many("ekids.hocsinh_ca_canthiep", "hocsinh_id"
                                       , string="Thiết lập [Ca] can thiệp trong tuần")
    nghiphep_ids = fields.One2many("ekids.hocsinh_nghiphep", "hocsinh_id"
                                      , string="Quản lý ngày nghỉ của học sinh")

    is_taikhoan = fields.Boolean(string="Đã có tài khoản", compute="_compute_is_taikhoan")

    hocphi_ids = fields.One2many("ekids.hocphi", "hocsinh_id",
                                string="Học phí hàng tháng")
    phuhuynh_ids = fields.One2many("ekids.hocsinh_phuhuynh", "hocsinh_id",
                                 string="Thông tin phụ huynh")
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'ekids_hocsinh_giayto2ir_attachments_rel',
        'hocsinh_id',
        'attachment_id',
        string="Hồ sơ/giấy tờ"
    )
    lichsu_canthiep_ids = fields.One2many("ekids.hocsinh_lichsu_canthiep", "hocsinh_id",
                                        string="Quá trình học tập/can thiệp")

    is_hoanthien_hoso = fields.Boolean(string="Hồ sơ",default=False)

    _sql_constraints = [
        ('ekids_hocsinh_unique_user_id', 'unique(user_id)', 'Học sinh chỉ có một tài khoản !')
    ]

    @api.depends('name')
    def _compute_ten(self):
        for record in self:
            if record.name:
                last_word = record.name.strip().split()[-1]
                record.ten = last_word
            else:
                record.ten= record.bietdanh
    @api.depends('user_id')
    def _compute_is_taikhoan(self):
        for record in self:
            if record.user_id:
                record.is_taikhoan = True
            else:
                record.is_taikhoan = False




    @api.depends('ngaysinh')
    def _compute_hocsinh_tuoi(self):
        now = datetime.today()
        for hs in self:
            if hs.ngaysinh:
                tong_thang = (now.year - hs.ngaysinh.year) * 12 + (now.month - hs.ngaysinh.month)
                if now.day < now.day:
                    tong_thang -= 1
                nam = tong_thang // 12
                thang = tong_thang % 12
                tuoi = ""
                if nam >=1:
                    tuoi += str(nam) +" tuổi "
                if thang >=1:
                    tuoi += str(thang) +" tháng"
                hs.tuoi=tuoi
            else:
                hs.tuoi ='0'

    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            coso = None
            coso_id = self.env.context.get('default_coso_id') or vals.get('coso_id')
            if coso_id:
                vals['coso_id'] = coso_id
                coso = self.env['ekids.coso'].browse(coso_id)

            if coso and coso.exists() and coso.ma:
                ma =self.func_get_hocsinh_ma(coso)
                vals['ma'] = ma
            else:
                raise ValidationError(_("Không thể tạo mã [Học sinh] vì thiếu mã cơ sở (ma_coso)."))

            records.append(super(HocSinh, self).create(vals))
            return records[0] if len(records) == 1 else records


    # Bổ sung group by du trạng thái không có và hiển thị list có phân loại theo trạng thái
    @api.model
    def func_get_hocsinh_ma(self,coso):
        day =date.today()
        year = day.year
        code = coso.ma+".hocsinh."+str(year)
        seq = (self.env['ir.sequence']
               .search([('code', '=', code)], limit=1))
        if not seq:
            data ={
                'name': f"Sequence for {code}",
                'code': code,
                'prefix': "%(y)s.",
                'padding': 3,
                'number_next': 1,
                'number_increment': 1,
            }
            seq = self.env['ir.sequence'].sudo().create(data)
        return seq.next_by_id()

    @api.model
    def action_global_report(self):
        # KHÔNG sử dụng self vì không có active_ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tất cả học sinh',
            'res_model': 'school.student',
            'view_mode': 'tree,form',
            'target': 'new',
        }


    def action_mo_popup_taikhoan_phuhuynh(self):
        self.ensure_one()
        form_view_id = self.env.ref('ekids_hocsinh.view_ekids_hocsinh_user_form').id
        if self.id:
            return {
                'type': 'ir.actions.act_window',
                'name': ('Thông tin tài khoản'),
                'res_model': 'res.users',
                'view_mode': 'form',
                'views': [(form_view_id,'form')],
                'res_id':self.user_id.id,
                'target': 'new',
                'context':{
                    'hocsinh_id': self.id,

                },
            }


    def action_view_kehoach_hocsinh(self):
        self.ensure_one()
        kanban_view_id = self.env.ref('ekids_hocsinh.kehoach_kanban_view').id
        form_view_id = self.env.ref('ekids_hocsinh.kehoach_form').id  # chú ý id chính xác

        return {
            'type': 'ir.actions.act_window',
            'name': 'KẾ HOẠCH [CAN THIỆP]',
            'res_model': 'ekids.kehoach',
            'view_mode': 'kanban,form',
            'views': [
                (kanban_view_id, 'kanban'),
                (form_view_id, 'form')
            ],
            'target': 'current',
            'context': dict(
                self.env.context,
                default_hocsinh_id=self.id,
                default_coso_id=self.coso_id.id,
                allowed_trangthai= ['0', '1','2','3','4'],
            ),
        }

    def action_xoa_taikhoan_hocsinh(self):
        user = self.user_id
        if user:
            self.user_id = False
            self.is_taikhoan = False
            user.unlink()

    def action_nap_rut_tien(self):
        self.ensure_one()  # Đảm bảo đang đứng ở 1 bản ghi học sinh cụ thể
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tạo/Nạp tiền vào tài khoản Học sinh',
            'res_model': 'ekids.taichinh_lichsu_giaodich',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_hocsinh_id': self.id,  # Truyền ID học sinh hiện tại
                'default_ngay': fields.Date.context_today(self),  # Truyền ngày hôm nay chuẩn múi giờ
                # Bổ sung cờ lênh reload cho Web Client Odoo 18
                'flags': {'mode': 'form', 'action_buttons': True, 'on_close': 'reload'},
            }
        }

    def action_xem_lichsu_giaodich(self):
        self.ensure_one()  # Đảm bảo đang đứng ở 1 bản ghi học sinh cụ thể
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tạo/Nạp tiền vào tài khoản Học sinh',
            'res_model': 'ekids.taichinh_lichsu_giaodich',
            'view_mode': 'list',
            'target': 'new',
            'domain': [('hocsinh_id', '=', self.id)],  # BỘ LỌC: Chỉ lấy giao dịch của học sinh này
            'context': {
                'default_hocsinh_id': self.id,  # Truyền ID học sinh hiện tại
            }
        }






