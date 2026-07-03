from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
import re
from bs4 import BeautifulSoup

import logging
_logger = logging.getLogger(__name__)


try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")





class MucTieu(models.Model):
    _name = "ekids.ct_muctieu"
    _description = "Lĩnh vực"
    _order = "sequence asc,id desc"

    coso_id = fields.Many2one("ekids.coso", related="linhvuc_id.coso_id", string="Cơ sở", required=True,ondelete="restrict")
    chuongtrinh_id = fields.Many2one("ekids.ct_chuongtrinh", related="linhvuc_id.chuongtrinh_id", string="Chương trình", required=True,
                              ondelete="restrict")
    # Trường này chỉ dùng để hứng dữ liệu từ Excel lúc Import, không lưu vào Postgres
    import_chuongtrinh_name = fields.Char(string="Tên chương trình import", store=False)

    sequence = fields.Integer(string="STT", default=1)
    index = fields.Integer(string="STT hiển thị", compute="_compute_index", store=False)
    index_list = fields.Integer(string="STT hiển thị", compute="_compute_index_list", store=False)
    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực',required=True)
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi',required=True)

    name = fields.Char(string="Tên",required=True)
    chucnang = fields.Html(string="Chức năng phát triển cốt lõi & Lập luận lâm sàng")
    thietke = fields.Html(string="Thiết kế hoạt động cho giáo viên Theo mô tả (ABC)")
    tieuchi_chuadat = fields.Char(string="Chưa đạt (-)")
    tieuchi_hinhthanh = fields.Char(string="Đang hình thành (+/-)")
    tieuchi_dat = fields.Char(string="Đạt (+)")

    trangthai = fields.Selection([("0", "Không hoạt động")
                                     , ("1", "Đang hoạt động")], default="1", required=True)

    is_thangtruoc = fields.Boolean(string="Dữ liệu từ tháng trước",compute="_compute_is_thangtruoc",store=False)

    @api.depends('linhvuc_id', 'sequence')
    def _compute_index(self):
        # 1. Gom nhóm các bản ghi thực tế đang hiển thị trên màn hình theo từng Lĩnh vực
        linhvuc_groups = {}
        for rec in self:
            linhvuc_groups.setdefault(rec.linhvuc_id.id, []).append(rec)

        # 2. Sắp xếp tuyến tính nội bộ từng nhóm và đánh số thứ tự từ 1 trở đi
        for lv_id, rec_list in linhvuc_groups.items():
            # Sắp xếp danh sách dựa trên sequence và id để đảm bảo thứ tự kéo thả không đổi
            sorted_list = sorted(rec_list, key=lambda r: (r.sequence, r.id))

            for idx, rec in enumerate(sorted_list, 1):
                rec.index = idx

    def _compute_is_thangtruoc(self):
        muctieu_thangtruoc_ids = self.env.context.get('default_muctieu_thangtruoc_ids')
        for record in self:
            is_thangtruoc = False
            if (muctieu_thangtruoc_ids and record.id in muctieu_thangtruoc_ids):
                is_thangtruoc = True
            record.is_thangtruoc = is_thangtruoc

    def action_xoa_muctieu_khoi_wizard(self):
        """
        Nút bấm chạy tại model con, nhưng xử lý gỡ liên kết trên model cha Wizard
        """
        self.ensure_one()

        # 🌟 BƯỚC 1: Bốc ID của Form cha Wizard đang mở ngoài màn hình từ Context
        wizard_id = self.env.context.get('default_wizard_id')
        # Kiểm tra phòng hờ xem nút này có đúng là được bấm từ giao diện Wizard cha không
        if wizard_id:
            wizard = self.env['ekids.kehoach_linhvuc_wizard'].browse(wizard_id)

            if wizard.exists():
                # 🌟 BƯỚC 2: Ra lệnh cho Wizard gỡ liên kết Many2many của mục tiêu hiện tại (self.id)
                # Lệnh (3, self.id) chỉ gỡ mối quan hệ Many2many trên RAM/Giao diện ảo, không xóa DB
                wizard.write({
                    'muctieu_ids': [(3, self.id, 0)]  # 3 có nghĩa là: Chỉ gỡ mối quan hệ này ngoài UI, không xóa vật lý
                })

                # 🌟 BƯỚC 3: Trả về Action nạp lại chính Wizard để làm tươi (Refresh) lưới giao diện phẳng mịn
                kehoach_linhvuc= wizard.kehoach_linhvuc_id
                if kehoach_linhvuc:
                    url_back= kehoach_linhvuc.action_xem_danhsach_ct_muctieu()
                    if url_back:
                        return url_back

        return True


    def _compute_index_list(self):
        index =1
        for record in self:
            record.index_list = index
            index +=1

    def action_luachon_ct_muctieu_vao_kehoach(self):
        self.ensure_one()  # Xử lý đích danh dòng vừa được bấm nút

        # Bốc các ID cấu trúc được truyền từ context ngầm của nút cha
        kehoach_id = self.env.context.get('default_kehoach_id')
        linhvuc_id = self.env.context.get('default_linhvuc_id')
        tuoi_id = self.env.context.get('default_tuoi_id')

        return self.action_chon_kehoach_muctieu()



    def action_chon_kehoach_muctieu(self):
        # Lấy ID của danh sách list view danh mục mục tiêu mẫu
        list_view_id = self.env.ref('ekids_canthiep.ct_muctieu_list').id

        return {
            'type': 'ir.actions.act_window',
            'name': 'LỰA CHỌN MỤC TIÊU CHO KẾ HOẠCH',
            'res_model': 'ekids.ct_muctieu',
            'view_mode': 'list',  # 🌟 SỬA TỪ 'form' THÀNH 'list' để hiện danh sách
            'views': [(list_view_id, 'list')],  # Chuẩn Odoo 18
            'target': 'new',  # Mở dạng Pop-up
            'context': {
                # Ép bộ lọc tự động chỉ hiển thị các mục tiêu thuộc Lĩnh vực và Độ tuổi này
                'search_default_linhvuc_id': self.linhvuc_id.id,
                'search_default_tuoi_id': self.tuoi_id.id,

                'edit': False,  # 🚫 Tắt hoàn toàn tính năng và ẩn nút [Sửa]
                'create': False,  # 🚫 Tắt tính năng và ẩn nút [Tạo mới]
                'delete': False,  # 🚫 Tắt tính năng và ẩn nút [Xóa]
            },
        }


    def action_chon_muctieu_vao_kehoach(self):
        kehoach_linhvuc_id = self.env.context.get("default_kehoach_linhvuc_id")
        if kehoach_linhvuc_id:
            kehoach_linhvuc =self.env['ekids.kehoach_linhvuc'].browse(kehoach_linhvuc_id)
            if kehoach_linhvuc:
               kehoach_linhvuc.func_tao_kehoach_muctieu(self)
               url = kehoach_linhvuc.action_them_muctieu_vao_kehoach_linhvuc()
               if url:
                   return url


        return None


    @api.model
    def load(self, fields_list, data):
        """
        Hàm can thiệp ngầm vào luồng Import Excel của Odoo 18.
        Tự động map trúng Lĩnh vực dựa theo điều kiện lọc của Chương trình.
        """
        # Kiểm tra xem file Excel tải lên có chứa đồng thời cả 2 cột Chương trình và Lĩnh vực không
        if 'linhvuc_id' in fields_list and  'tuoi_id' in fields_list:
            linhvuc_idx = fields_list.index('linhvuc_id')
            tuoi_idx = fields_list.index('tuoi_id')
            chuongtrinh_idx = fields_list.index('import_chuongtrinh_name')

            chucnang_idx = fields_list.index('chucnang')
            thietke_idx = fields_list.index('thietke')

            # 🌟 MẸO CHÍ MẠNG: Ép Odoo đổi kiểu map cột Lĩnh vực từ Tên chữ sang ID số hệ thống
            fields_list[linhvuc_idx] = 'linhvuc_id/.id'
            fields_list[tuoi_idx] = 'tuoi_id/.id'

            # Duyệt qua từng hàng dữ liệu trong file Excel giáo viên tải lên
            for row in data:

                linhvuc_name = row[linhvuc_idx]  # Ví dụ: "Vận động"
                tuoi_name = row[tuoi_idx]  # Ví dụ: "Vận động"
                ct_name = row[chuongtrinh_idx]
                if linhvuc_name and tuoi_name:
                    # Truy vấn chính xác Lĩnh vực thuộc Chương trình tương ứng
                    linhvuc = self.env['ekids.ct_linhvuc'].search([
                        ('name', '=', linhvuc_name),
                        ('chuongtrinh_id.name', 'ilike', ct_name)  # Đổi từ '=' sang 'ilike'
                    ], limit=1)



                    if linhvuc:
                        # Ghi đè chữ "Vận động" thành ID số (ví dụ: 45) để Odoo nạp thẳng, không bị nhận nhầm
                        row[linhvuc_idx] = linhvuc.id
                    else:
                        # Nếu ghi sai tên, trả về False để Odoo báo lỗi dòng đó trực quan
                        row[linhvuc_idx] = False

                    tuoi = self.env['ekids.ct_tuoi'].search([
                        ('name', '=', tuoi_name),
                        ('chuongtrinh_id.name', 'ilike', ct_name)  # Đổi từ '=' sang 'ilike'
                    ], limit=1)

                    if tuoi:
                        # Ghi đè chữ "Vận động" thành ID số (ví dụ: 45) để Odoo nạp thẳng, không bị nhận nhầm
                        row[tuoi_idx] = tuoi.id
                    else:
                        # Nếu ghi sai tên, trả về False để Odoo báo lỗi dòng đó trực quan
                        row[tuoi_idx] = False
                    chuongtrinh = self.func_giulai_format_exel_to_html(row[chucnang_idx])
                    row[chucnang_idx] =chuongtrinh
                    thietke =self.func_giulai_format_exel_to_html(row[thietke_idx])
                    row[thietke_idx] = thietke



        # Trả luồng về cho Odoo xử lý bulk create tiếp tục
        return super(MucTieu, self).load(fields_list, data)


    def func_giulai_format_exel_to_html(self,text):
        formatted_value = text.replace('\r\n', '\n').replace('\n', '<br/>')

        # 2. XỬ LÝ BÔI ĐẬM TỰ ĐỘNG BẰNG REGEX (Theo quy ước dấu *)
        # Biến đổi cấu trúc *Chữ bôi đậm* thành <b>Chữ bôi đậm</b>
        formatted_value = re.sub(r'\*(.*?)\*', r'<b>\1</b>', formatted_value)

        # 3. THÊM XỬ LÝ IN NGHIÊNG TỰ ĐỘNG BẰNG REGEX (Theo quy ước dấu _)
        # Biến đổi cấu trúc _Chữ in nghiêng_ thành <i>Chữ in nghiêng</i>
        formatted_value = re.sub(r'_(.*?)_', r'<i>\1</i>', formatted_value)

        # 4. TỰ ĐỘNG BÔI ĐẬM CÁC TIÊU ĐỀ ĐẦU DÒNG (Phần trước dấu hai chấm)
        formatted_value = re.sub(r'(^|<br/>)([^:\n<]+:)', r'\1<b>\2</b>', formatted_value)

        return formatted_value




