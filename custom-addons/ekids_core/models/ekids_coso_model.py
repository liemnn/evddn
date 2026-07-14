from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
class CoSo(models.Model):
    _name = "ekids.coso"
    _description = "Mô tả về cơ sở "

    logo = fields.Binary(string="Logo")
    slogan =fields.Char(string="Slogan")

    ma= fields.Char(string="Mã",required=True)
    name = fields.Char(string='Tên viết tắt',  required=True, index='trigram')
    fullname = fields.Char(string='Tên đầy đủ',  required=True)
    masothue = fields.Char(string="Mã số thuế")
    cha_id = fields.Many2one("ekids.coso",string="Trực thuộc")
    desc =fields.Html(string="Mô tả")
    dm_tinh_id =fields.Many2one("ekids.dm_tinh",string="Tỉnh",required=True)
    dm_xa_id = fields.Many2one("ekids.dm_xa", string="Xã",domain="[('dm_tinh_id','=',dm_tinh_id)]",required=True)
    diachi_chitiet =fields.Char(string="Số nhà/ đường phố, thôn xóm")
    email = fields.Char(string="Email")
    dienthoai = fields.Char(string="Số điện thoại liên hệ",required=True)
    coso_ids = fields.One2many('ekids.coso', 'cha_id')
    user_id = fields.Many2one("res.users",string="Tài khoản quản trị cơ sở")


    thue_tungay = fields.Date(string="Ngày bắt đầu thuê",required=True)
    thue_denngay = fields.Date(string="Ngày kết thúc thuê")
    trangthai = fields.Selection([("0", "Đang cấu hình (chưa thuê)")
                                     ,("1", "Đang thuê")
                                     , ("-1", "Hết thời gian thuê ( tạm dừng)")],
                            string="Trạng thái",compute="_compute_trangthai",store=True)

    tyle_tralai_hs_nghiphep = fields.Integer(string="Tỷ lệ % khi Học sinh xin [Nghỉ phép]", default=0,
                                         required=True)
    tyle_tralai_coso_chonghi = fields.Integer(string="Tỷ lệ % khi Nhà trường cho nghỉ", default=0,
                                             required=True)
    tyle_tralai_hs_vangmat = fields.Integer(string="Tỷ lệ % khi Học sinh [Vắng mặt]", default=0,
                                             required=True)

    hd_t2 = fields.Boolean(string="T2")
    hd_t3 = fields.Boolean(string="T3")
    hd_t4 = fields.Boolean(string="T4")
    hd_t5 = fields.Boolean(string="T5")
    hd_t6 = fields.Boolean(string="T6")
    hd_t7 = fields.Boolean(string="T7")
    hd_t8 = fields.Boolean(string="CN")

    is_admin = fields.Boolean(
        default=lambda self: self.env.user.has_group('base.group_system'),
        store=False
    )

    header_thu_hocphi = fields.Html(string="Tiêu đề [Phần đầu] Phiếu [Học phí/Lương]")

    ghichu_thu_hocphi = fields.Html(string="Ghi chú [Phần cuối] Phiếu [Học phí]")
    qrcode_thu_hocphi = fields.Binary(string="QR-Code [Chuyển khoản] thu Học phí")


    bank_bin = fields.Selection(
        selection='_get_vietnam_banks',
        string="Ngân hàng thụ hưởng",
        required=True
    )
    bank_acc_number = fields.Char("Số tài khoản")


    is_thu_hocphi_dauthang =fields.Boolean(string="Thiết lập thu [Học phí] đầu tháng",default=True)
    is_dong_hocphi_theoky= fields.Boolean(string="Đóng học phí theo kỳ/Gộp kỳ", default=False)

    sothang_khoa_dl_chitieu = fields.Selection(
        [('0', 'Không khóa'),('1', '1 Tháng'), ('2', '2 Tháng'), ('3', '3 Tháng'), ('4', '4 Tháng'), ('5', '5 Tháng'),
         ('6', '6 Tháng'), ('7', '7 Tháng'), ('8', '8 Tháng'), ('9', '9 Tháng'), ('10', '10 Tháng'),
         ('11', '11 Tháng'), ('12', '12 Tháng')],
        string='Sẽ khóa dữ liệu [Chi/Tiêu] sau số tháng',
        default='0',
        required=True
    )

    sothang_khoa_dl_diemdanh= fields.Selection(
        [('0', 'Không khóa'), ('1', '1 Tháng'), ('2', '2 Tháng'), ('3', '3 Tháng'), ('4', '4 Tháng'), ('5', '5 Tháng'),
         ('6', '6 Tháng'), ('7', '7 Tháng'), ('8', '8 Tháng'), ('9', '9 Tháng'), ('10', '10 Tháng'),
         ('11', '11 Tháng'), ('12', '12 Tháng')],
        string='Sẽ khóa dữ liệu [Điểm danh/Chấm công]sau số tháng',
        default='0',
        required=True
    )

    trangthai_hocphi_khoa_dl = fields.Text(string="Thiết lập Trạng thái [Học phí] cho phép sửa dữ liệu",default="")
    trangthai_luong_khoa_dl = fields.Char(string="Thiết lập Trạng thái [Lương] cho phép sửa dữ liệu",default="")

    cauhinh = fields.Text(string="Thiết lập cấu hình cho Cơ sở", default="")

    def _get_vietnam_banks(self):
        return [
            ('422589', 'CIMB (Ngân hàng TNHH MTV CIMB Việt Nam)'),
            ('458761', 'HSBC (Ngân hàng TNHH MTV HSBC (Việt Nam))'),
            ('533948', 'Citibank (Ngân hàng Citibank, N.A. - Chi nhánh Hà Nội)'),
            ('546034', 'CAKE (TMCP Việt Nam Thịnh Vượng - Ngân hàng số CAKE by VPBank)'),
            ('546035', 'Ubank (TMCP Việt Nam Thịnh Vượng - Ngân hàng số Ubank by VPBank)'),
            ('668888', 'KBank (Ngân hàng Đại chúng TNHH Kasikornbank)'),
            ('796500', 'DBSBank (DBS Bank Ltd - Chi nhánh Thành phố Hồ Chí Minh)'),
            ('801011', 'Nonghyup (Ngân hàng Nonghyup - Chi nhánh Hà Nội)'),
            ('963388', 'Timo (Ngân hàng số Timo by Ban Viet Bank)'),

            ('970400', 'SaigonBank (Ngân hàng TMCP Sài Gòn Công Thương)'),
            ('970405', 'Agribank (Ngân hàng Nông nghiệp và Phát triển Nông thôn Việt Nam)'),
            ('970406', 'Vikki (Ngân hàng TNHH MTV Số Vikki)'),
            ('970407', 'Techcombank (Ngân hàng TMCP Kỹ thương Việt Nam)'),
            ('970408', 'GPBank (Ngân hàng Thương mại TNHH MTV Dầu Khí Toàn Cầu)'),
            ('970409', 'BacABank (Ngân hàng TMCP Bắc Á)'),
            ('970410', 'StandardChartered (Ngân hàng TNHH MTV Standard Chartered Bank Việt Nam)'),
            ('970412', 'PVcomBank (Ngân hàng TMCP Đại Chúng Việt Nam)'),
            ('970414', 'MBV (Ngân hàng TNHH MTV Việt Nam Hiện Đại)'),
            ('970415', 'VietinBank (Ngân hàng TMCP Công thương Việt Nam)'),
            ('970416', 'ACB (Ngân hàng TMCP Á Châu)'),
            ('970418', 'BIDV (Ngân hàng TMCP Đầu tư và Phát triển Việt Nam)'),
            ('970419', 'NCB (Ngân hàng TMCP Quốc Dân)'),
            ('970421', 'VRB (Ngân hàng Liên doanh Việt - Nga)'),
            ('970422', 'MBBank (Ngân hàng TMCP Quân đội)'),
            ('970423', 'TPBank (Ngân hàng TMCP Tiên Phong)'),
            ('970424', 'ShinhanBank (Ngân hàng TNHH MTV Shinhan Việt Nam)'),
            ('970425', 'ABBANK (Ngân hàng TMCP An Bình)'),
            ('970426', 'MSB (Ngân hàng TMCP Hàng Hải Việt Nam)'),
            ('970427', 'VietABank (Ngân hàng TMCP Việt Á)'),
            ('970428', 'NamABank (Ngân hàng TMCP Nam Á)'),
            ('970429', 'SCB (Ngân hàng TMCP Sài Gòn)'),
            ('970430', 'PGBank (Ngân hàng TMCP Thịnh vượng và Phát triển)'),
            ('970431', 'Eximbank (Ngân hàng TMCP Xuất Nhập khẩu Việt Nam)'),
            ('970432', 'VPBank (Ngân hàng TMCP Việt Nam Thịnh Vượng)'),
            ('970433', 'VietBank (Ngân hàng TMCP Việt Nam Thương Tín)'),
            ('970434', 'IndovinaBank (Ngân hàng TNHH Indovina)'),
            ('970436', 'Vietcombank (Ngân hàng TMCP Ngoại thương Việt Nam)'),
            ('970437', 'HDBank (Ngân hàng TMCP Phát triển Thành phố Hồ Chí Minh)'),
            ('970438', 'BaoVietBank (Ngân hàng TMCP Bảo Việt)'),
            ('970439', 'PublicBank (Ngân hàng TNHH MTV Public Việt Nam)'),
            ('970440', 'SeABank (Ngân hàng TMCP Đông Nam Á)'),
            ('970441', 'VIB (Ngân hàng TMCP Quốc tế Việt Nam)'),
            ('970442', 'HongLeong (Ngân hàng TNHH MTV Hong Leong Việt Nam)'),
            ('970443', 'SHB (Ngân hàng TMCP Sài Gòn - Hà Nội)'),
            ('970444', 'CBBank (Ngân hàng Thương mại TNHH MTV Xây dựng Việt Nam)'),
            ('970446', 'COOPBANK (Ngân hàng Hợp tác xã Việt Nam)'),
            ('970449', 'LPBank (Ngân hàng TMCP Lộc Phát Việt Nam)'),
            ('970452', 'KienLongBank (Ngân hàng TMCP Kiên Long)'),
            ('970454', 'VietCapitalBank (Ngân hàng TMCP Bản Việt)'),
            ('970455', 'IBKHN (Ngân hàng Công nghiệp Hàn Quốc - Chi nhánh Hà Nội)'),
            ('970456', 'IBKHCM (Ngân hàng Công nghiệp Hàn Quốc - Chi nhánh TP. Hồ Chí Minh)'),
            ('970457', 'Woori (Ngân hàng TNHH MTV Woori Việt Nam)'),
            ('970458', 'UnitedOverseas (Ngân hàng United Overseas - Chi nhánh TP. Hồ Chí Minh)'),
            ('970462', 'KookminHN (Ngân hàng Kookmin - Chi nhánh Hà Nội)'),
            ('970463', 'KookminHCM (Ngân hàng Kookmin - Chi nhánh TP. Hồ Chí Minh)'),
            ('970466', 'KEBHanaHCM (Ngân hàng KEB Hana - Chi nhánh Thành phố Hồ Chí Minh)'),
            ('970467', 'KEBHanaHN (Ngân hàng KEB Hana - Chi nhánh Hà Nội)'),

            ('971005', 'ViettelMoney (Tổng Công ty Dịch vụ số Viettel)'),
            ('971011', 'VNPTMoney (VNPT Money)'),
            ('971025', 'MoMo (Công ty Cổ phần Dịch vụ Di động Trực tuyến)'),
            ('971133', 'PVcomBank Pay (Ngân hàng số PVcomBank Pay)'),
            ('977777', 'MAFC (Công ty Tài chính TNHH MTV Mirae Asset Việt Nam)'),
            ('999888', 'VBSP (Ngân hàng Chính sách Xã hội)'),
        ]

    @api.depends('thue_tungay', 'thue_denngay')
    def _compute_trangthai(self):
        today = date.today()
        for record in self:
            # Nếu thiếu 1 trong 2 ngày → xem như chưa thuê
            if not record.thue_tungay or not record.thue_denngay:
                record.trangthai = '0'  # Đang cấu hình (chưa thuê)
            elif record.thue_tungay > today:
                record.trangthai = '0'  # Chưa đến ngày thuê
            elif record.thue_tungay <= today <= record.thue_denngay:
                record.trangthai = '1'  # Đang thuê
            else:
                record.trangthai = '-1'  # Hết thời hạn

    @api.model
    def search_fetch(self, domain, field_names,offset=0, limit=50, order=None):
        # Lấy thông tin người dùng hiện tại
        user = self.env.user
        today = date.today()

        # Điều kiện lọc (ví dụ: chỉ cho phép xem các đơn hàng có đối tác là khách hàng của user)
        if user.has_group('base.group_system'):  # Kiểm tra nhóm quyền
            #TH1: là admin của toàn hệ thống
            domain = domain  # Thêm điều kiện cho
            return  super().search_fetch(domain,field_names,offset,limit,order)
        else:
            domain=[]
            # TH3: user khác của cơ sở ( thường là giáo viên được phân quyền)
            # sẽ tính trên danh sách các cơ sở được phân cho user này
            if user.coso_ids:
                ids=[]
                domain = domain
                #tinh toán trên danh sach cơ sở
                for coso in user.coso_ids:
                    thue_tungay = coso.thue_tungay
                    thue_denngay = coso.thue_denngay
                    if thue_denngay and thue_denngay and thue_tungay <= today <= thue_denngay:
                        ids.append(coso.id)
                if len(ids) > 0:
                    domain += [('id', 'in', ids)]
                else:
                    domain += [('id', '=', -1)]

            else:
                # tra về null cơ sở không cho phép nhìn thấy cơ sở nào
                domain += [('id', '=', -1)]

            return super().search_fetch(domain, field_names, offset, limit, order)

    def action_quanly_nghile_nam_cua_trungtam(self):
        day =date.today()
        year = day.year
        nghile_nam = self.env['ekids.nghile_nam'].search(
                 [('coso_id', '=', self.id)
                , ('name', '=', str(year))

                ],limit=1)
        if not nghile_nam:
            data ={
                'coso_id': self.id,
                'name': str(year)
            }
            nghile_nam =self.env['ekids.nghile_nam'].create(data)

        return {
            'type': 'ir.actions.act_window',
            'name': 'NGHỈ LỄ',
            'res_model': 'ekids.nghile_nam',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id
            }
        }

    def action_thietlap_cauhinh_bandau_cua_trungtam(self):
        self.ensure_one()
        form_view_id = self.env.ref('ekids_core.coso_form_setting_view').id  # chú ý id chính xác

        return {
            'type': 'ir.actions.act_window',
            'name': 'THIẾT LẬP- THÔNG TIN CƠ SỞ',
            'res_model': 'ekids.coso',
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'target': 'current',
            'res_id': self.id,
            'context': dict(
                self.env.context,

            ),
        }

    def action_gui_thongbao_phuhuynh(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'THÔNG BÁO-PHỤ HUYNH',
            'res_model': 'ekids.thongbao',
            'view_mode': 'list,kanban,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id
            }
        }





