from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from .ekids_hocphi_thang_abstractmodel import HocPhiThangAbstractModel

import uuid
import calendar

class HocPhi(models.Model,HocPhiThangAbstractModel):
    _name = 'ekids.hocphi'
    _description = 'Học phí của học sinh'
    _order = "hocsinh_id asc"

    # Khai báo các trường dữ liệu
    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    sequence = fields.Integer(string="TT", compute="_compute_sequence")
    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh", required=True, ondelete="restrict",index=True)
    thang_id = fields.Many2one('ekids.hocphi_thang', string='Học phí tháng',readonly=True,ondelete="restrict",index=True)
    nam_id = fields.Many2one('ekids.hocphi_nam', related="thang_id.nam_id", string='Năm', required=True,index=True,
                             ondelete="restrict")

    trangthai = fields.Selection([("-1", "Đang tính")
                                  ,("0", "Đã kiểm tra")
                                  ,("10", "Đã đóng[Tiền mặt]")
                                  ,("11", "Đã đóng[Chuyển khoản]")
                                  ,("12", "Đã đóng[Ví học sinh]")
                                  ,("2", "Nợ học phí")],default='-1')

    is_show_tinhtoan_lai = fields.Boolean(compute="_compute_is_show_tinhtoan_lai")



    hocphi_bantru_ids =fields.One2many("ekids.hocphi_bantru","hocphi_id"
                                       ,string="Thuộc học phí")
    hocphi_ca_ids = fields.One2many("ekids.hocphi_ca",
                                    "hocphi_id", string="Thuộc học phí ca")

    hocphi_duoctru_ids = fields.One2many("ekids.hocphi_duoctru",
                                         "hocphi_id", string="Các khoảng được trừ từ tháng trước")

    ngay_dihoc = fields.Integer(string="Số ngày đi học", default=0)
    ngay_dihoc_coso = fields.Integer(string="Số ngày đi học", default=0)
    songay_dihoc = fields.Char(string="Ngày đi học", compute="_compute_songay_dihoc")

    tien_bantru = fields.Float(string='(1).Lớp chung'
                            ,digits=(10, 0)
                            ,readonly=True
                            ,store=True
                            ,compute="_compute_tien_bantru")
    tien_ca = fields.Float(string='(2).Can thiệp'
                            , digits=(10, 0)
                            , readonly=True
                            ,store=True
                            ,compute="_compute_tien_ca")
    tien_duoctru = fields.Float(string='(3). Được trừ'
                            , digits=(10, 0)
                            , readonly=True
                            ,store=True
                            , compute="_compute_tien_duoctru")

    hocphi = fields.Float(string='Học phí = (1) + (2) - (3)'
                                ,digits=(10, 0)
                                ,readonly=True,
                                store=True,
                                compute="_compute_hocphi")

    tyle_giamhocphi = fields.Integer(string=" % Giảm",default=0)
    dm_chinhsach_giam_id = fields.Many2one("ekids.hocphi_dm_chinhsach_giam",
                                           string="Học sinh thuộc chính sách giảm học phí (nếu có)")
    is_giamhocphi_dacthu = fields.Boolean(string="Giảm học phí theo đặc thù",default=False)

    tyle_giamhocphi_bantru = fields.Integer(string=" % Giảm bán trú", default=0)
    tyle_giamhocphi_ca = fields.Integer(string=" % Giảm bán ca", default=0)

    hocphi_giam = fields.Float(string='(4).Được giảm'
                          , digits=(10, 0)
                          , readonly=True,
                          store=True,
                          compute="_compute_hocphi_giam")

    hocphi_phaidong = fields.Float(string='Thực đóng'
                          , digits=(10, 0)
                          , readonly=True,
                          store=True,compute="_compute_hocphi_phaidong")

    # làm access token  để chia sẻ
    access_token = fields.Char(string="Thẻ truy cập nhanh")
    share_url = fields.Char("Chi sẻ phiếu thu Học phí(URL)", compute="_compute_share_url",store=True)

    is_dong_hocphi_theoky = fields.Boolean(compute="_compute_is_dong_hocphi_theoky")

    def _compute_is_dong_hocphi_theoky(self):
        for record in self:
            if record.coso_id.is_dong_hocphi_theoky == True:
                record.is_dong_hocphi_theoky = True
            else:
                record.is_dong_hocphi_theoky = False


    def _compute_sequence(self):
        index =1
        for record in self:
            record.sequence = index
            index +=1

    def _compute_songay_dihoc(self):
        for record in self:
            record.songay_dihoc = str(record.ngay_dihoc)+"/"+str(record.ngay_dihoc_coso)

    @api.depends("trangthai")
    def _compute_is_show_tinhtoan_lai(self):

        for record in self:
            if record.trangthai=="-1":
                record.is_show_tinhtoan_lai = True
            else:
                record.is_show_tinhtoan_lai =False


    @api.depends("hocphi")
    def _compute_share_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for rec in self:
            rec.access_token = str(uuid.uuid4())
            rec.share_url = rec.access_token and f"{base_url}/hocphi/{rec.access_token}" or False



    #bổ sung groupby hiển thị học phí dù trạng thái đó không có
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        result = super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        if 'trangthai' in groupby:
            selection_values = dict(self._fields['trangthai'].selection)
            existing_keys = [group['trangthai'] for group in result if group['trangthai'] is not False]

            for key, label in selection_values.items():
                if key not in existing_keys:
                    result.append({
                        'trangthai': key,
                        'trangthai_count': 0,
                        '__domain': domain + [('trangthai', '=', key)],
                    })
        return result

    @api.constrains('coso_id','hocsinh_id','thang_id')
    def _check_unique_hocphi_hocsinh(self):
        for record in self:
            # Tìm các bản ghi khác có cùng 'code'
            count = self.env['ekids.hocphi'].search_count([
                ('id', '!=', record.id),
                ('coso_id', '=', record.coso_id.id),
                ('hocsinh_id', '=', record.hocsinh_id.id),
                ('thang_id', '=', record.thang_id.id)
            ])
            if count >0:
                raise ValidationError("Học sinh đã được tạo học phí tại tháng này. Vui lòng kiểm tra lại.")






    @api.depends("hocphi_bantru_ids")
    def _compute_tien_bantru(self):
        for hp in self:
            if hp.hocphi_bantru_ids:
                tong = 0
                for c in hp.hocphi_bantru_ids:
                    tong += c.tien
                hp.tien_bantru = tong

            else:
                hp.tien_bantru = 0

    @api.depends("hocphi_ca_ids")
    def _compute_tien_ca(self):
        for hp in self:
            if hp.hocphi_ca_ids:
                tong = 0
                for c in hp.hocphi_ca_ids:
                    tong += c.tien
                hp.tien_ca = tong

            else:
                hp.tien_ca = 0

    @api.depends("hocphi_duoctru_ids")
    def _compute_tien_duoctru(self):
        for hp in self:
            if hp.hocphi_duoctru_ids:
                tong = 0
                for c in hp.hocphi_duoctru_ids:
                    tong += c.tien
                hp.tien_duoctru = tong

            else:
                hp.tien_duoctru = 0

    @api.depends("hocphi_bantru_ids","hocphi_ca_ids","hocphi_duoctru_ids")
    def _compute_hocphi(self):
        for hp in self:
            hp.hocphi = (hp.tien_bantru +hp.tien_ca) - hp.tien_duoctru
            hp.hocphi_phaidong = hp.hocphi - hp.hocphi_giam


    @api.depends("hocphi_bantru_ids", "hocphi_ca_ids", "hocphi_duoctru_ids","tyle_giamhocphi","is_giamhocphi_dacthu","tyle_giamhocphi_bantru","tyle_giamhocphi_ca")
    def _compute_hocphi_giam(self):
        for hp in self:
            if hp.is_giamhocphi_dacthu == True:
                # Giam theo tong khong chia tung khoan rieng
                # tyle giảm bán trú
                tyle_bantru = hp.tyle_giamhocphi
                tyle_ca = hp.tyle_giamhocphi
                if hp.is_giamhocphi_dacthu == True:
                    tyle_bantru = hp.tyle_giamhocphi_bantru
                    tyle_ca = hp.tyle_giamhocphi_ca

                bantru = hp.func_hocphi_giam_bantru()
                # tong giảm ca can thiệp
                ca = hp.func_hocphi_giam_ca()
                # tổng giảm
                hocphi = hp.hocphi
                hocphi_giam = (bantru + ca) - hp.tien_duoctru
                tien_giam = ((bantru/100)* tyle_bantru) +((ca/100)* tyle_ca)
                hp.hocphi_giam = tien_giam
                hp.hocphi_phaidong = hocphi - hocphi_giam
            else:
                # Giam theo tong khong chia tung khoan rieng
                bantru = hp.func_hocphi_giam_bantru()
                # tong giảm ca can thiệp
                ca = hp.func_hocphi_giam_ca()
                tien_duoctru = hp.tien_duoctru
                hocphi = (bantru + ca) - tien_duoctru
                sotien_giam = (hocphi / 100) * hp.tyle_giamhocphi
                hp.hocphi_giam = sotien_giam
                hp.hocphi_phaidong = hocphi - sotien_giam




    def func_hocphi_giam_bantru(self):
        hocphi_bantru_ids = self.hocphi_bantru_ids
        if hocphi_bantru_ids:
            tong =0
            for hocphi_bantru_id  in hocphi_bantru_ids:
                if hocphi_bantru_id.dm_thu_bantru_id.is_giam_hocphi == True:
                    tong += hocphi_bantru_id.tien

            return tong


        return 0

    def func_hocphi_giam_ca(self):
        hocphi_ca_ids = self.hocphi_ca_ids
        if hocphi_ca_ids:
            tong =0

            for hocphi_ca_id  in hocphi_ca_ids:
                if hocphi_ca_id.dm_ca_id.is_giam_hocphi == True:
                    tong +=hocphi_ca_id.tien

            return tong


        return 0



    @api.depends("hocphi_bantru_ids","hocphi_ca_ids","hocphi_duoctru_ids","hocphi_giam")
    def _compute_hocphi_phaidong(self):
        for hp in self:
            hp.hocphi_phaidong = hp.hocphi - hp.hocphi_giam


    def action_xacthuc_tinhlai_hocphi_theo_thang(self):
        context = self.env.context
        coso_id = context.get("default_coso_id")
        thang = context.get("default_thang")
        nam = context.get("default_nam")

        #B1 xóa toàn bộ học phí tháng này của co so
        hocphis = self.env['ekids.hocphi'].search([
                ('coso_id', '=',coso_id),
                ('thang_id', '=',str(thang)),
                ('nam_id', '=', str(nam))
         ])
        if hocphis:
            for hocphi in hocphis:
                if hocphi.trangthai=='-1':
                    # Chỉ xóa và tính lại học phí Đang tính toán
                    hocphi.unlink()

        # B2 Tao lai default
        hocphi_thang= self.env['ekids.hocphi_thang'].search([
            ('coso_id', '=', coso_id),
            ('name', '=', str(thang)),
            ('nam_id', '=', str(nam))
        ])
        if hocphi_thang:
            hocphi_thang.action_view_khoitao_hocphi_hocsinh()

    def action_xacthuc_tinhlai_hocphi_hocsinh(self):
        self.func_tinhtoan_lai_hocphi_cho_mot_hocsinh()

    def action_in_hocphi(self):
        """Gọi report đã khai báo"""
        return (self.env.ref("ekids_hocsinh.action_phieuthus")
                .report_action(self))

    def action_in_ban_xacnhan(self):
        """Gọi report đã khai báo"""
        context = self.env.context
        coso_id = context.get("default_coso_id")
        thang = context.get("default_thang")
        nam = context.get("default_nam")
        return {
            'type': 'ir.actions.act_window',
            'name': 'In bản xác nhận',
            'res_model': 'ekids.hocphi_banin',
            'view_mode': 'form',
            'target': 'new',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': coso_id,
                'default_thang': thang,
                'default_nam': nam

            }
        }

    def action_chuyen_trangthai(self, trangthai):
        for record in self:
            record.write({'trangthai': trangthai})


    def action_dong_hocphi_qua_tien_hocsinh(self):
        #B1: lấy ve danh sach lich su giao dich thang nay
        giaodich_cuoi = self.env['ekids.taichinh_lichsu_giaodich'].search([
            ('hocsinh_id', '=', self.hocsinh_id.id),
            ('name', '=', str(self.nam_id.id)),
            ('thang', '=', str(self.thang_id.id))
        ],order='id desc',limit=1)
        is_dagiaodich= False
        if giaodich_cuoi:
            if giaodich_cuoi.hanhdong =='0':
                #giao dich hoan tiền  học phí
                liem=3




