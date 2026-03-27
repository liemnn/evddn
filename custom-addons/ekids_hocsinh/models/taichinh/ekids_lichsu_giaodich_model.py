from odoo import models, fields, api, _
from datetime import datetime, timedelta
from num2words import num2words
from odoo.exceptions import UserError


from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class LichSuGiaoDich(models.Model):

    _name = "ekids.taichinh_lichsu_giaodich"
    _description = "Lịch sử giao dịch"

    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh")
    name = fields.Char(string="Giao dịch")
    desc = fields.Text(string="Mô tả")
    ngay = fields.Date(string="Ngày")
    hanhdong = fields.Selection([("0", "Nạp tiền")
                                     ,("1", "Rút tiền")
                                    ], string="Hành động"
                                    ,default="0")

    tien = fields.Float(string='Số tiền(vnđ)'
                                , digits=(10, 0),default=0)
    # 1. Khai báo trường chứa chữ, tự động tính toán dựa vào 'sotien'
    sotien_bang_chu = fields.Char(string="Bằng chữ")
    sodu = fields.Float(string='Số dư(vnđ)',compute="_compute_sodu"
                        , digits=(10, 0), default=0,store=True)

    hocphi_thang = fields.Char(string="Học phí Tháng")
    hocphi_nam = fields.Char(string="Học phí Năm")
    # Bắt sự kiện: Cứ hễ ô 'sotien' thay đổi là hàm này chạy ngay lập tức
    @api.onchange('tien')
    def _onchange_sotien(self):
        # onchange không cần vòng lặp for rec in self vì nó chỉ chạy trên bản ghi đang mở ở giao diện
        self.func_tinhtoan_sodu_hientai()

        if self.tien:
            # 1. Dịch ra chữ tiếng Việt
            doc_chu = num2words(self.tien, lang='vi')

            # 2. Xử lý câu chữ cho hay: nghìn -> ngàn, thêm đuôi "đồng"
            doc_chu = doc_chu.replace('nghìn', 'ngàn') + ' đồng'

            # 3. Gán ngược lại vào ô chữ, viết hoa chữ cái đầu tiên
            self.sotien_bang_chu = doc_chu.capitalize()
        else:
            # Nếu người dùng xóa sạch số, thì xóa luôn dòng chữ
            self.sotien_bang_chu = False

    def func_tinhtoan_sodu_hientai(self):
        if self:
           hs =self.hocsinh_id
           tien_hien_tai = hs.tien or 0.0
           if self.hanhdong =='0':
               moi_sodu = tien_hien_tai + self.tien
           else:
               moi_sodu = tien_hien_tai - self.tien

           self.sodu =moi_sodu
    @api.model_create_multi
    def create(self, vals_list):
        # 1. Gom tất cả ID học sinh để đọc dữ liệu 1 lần (Optimize Performance)
        for vals in vals_list:
            hocsinh_id =vals['hocsinh_id']
            if hocsinh_id:
                hs = self.env['ekids.hocsinh'].browse(hocsinh_id)
                if hs:
                    # Lấy tiền hiện tại của học sinh
                    tien_hien_tai = hs.tien or 0.0
                    amount = float(vals.get('tien', 0))

                    # Kiểm tra đúng ký hiệu anh đã định nghĩa ở Selection (+ hoặc -)
                    if vals.get('hanhdong') == '0':
                        moi_sodu = tien_hien_tai + amount
                    else:
                        moi_sodu = tien_hien_tai - amount

                    # Gán số dư vào lịch sử giao dịch trước khi tạo
                    vals['sodu'] = moi_sodu

                    # Cập nhật ngược lại bảng Học sinh ngay lập tức
                    hs.write({'tien': moi_sodu})

        # 2. Gọi super chuẩn Odoo 18 (Trả về Recordset trực tiếp)
        return super(LichSuGiaoDich, self).create(vals_list)








