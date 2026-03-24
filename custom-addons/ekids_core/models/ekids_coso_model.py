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
                                     ,("1", "Đang thuê (sử dụng)")
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

    is_thu_hocphi_dauthang =fields.Boolean(string="Thiết lập thu [Học phí] đầu tháng",default=True)

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
            'view_mode': 'kanban,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id
            }
        }





