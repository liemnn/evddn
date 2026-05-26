from odoo import models, fields, api, exceptions
import re
from bs4 import BeautifulSoup


class MucTieu(models.Model):
    _name = "ekids.ct_muctieu"
    _description = "Lĩnh vực"

    sequence = fields.Integer(string="STT", default=1)
    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực')
    dm_capdo_id = fields.Many2one('ekids.ct_dm_capdo', string='Cấp độ')
    name = fields.Html(string="Mục tiêu [Can thiệp]")
    trichyeu = fields.Html(string="Trích yếu (mã)")
    kythuat = fields.Html(string="Kỹ thuật/chiến lược")
    tieuchi = fields.Html(string="Tiêu chí")
    cach_danhgia = fields.Html(string="Cách [Đánh giá]")



    @staticmethod
    def clean_html_text(html_text):
        # Phân tích HTML và lấy nội dung thuần văn bản
        soup = BeautifulSoup(html_text, "html.parser")
        text = soup.get_text(separator=' ')

        # Loại bỏ ký tự xuống dòng và dư thừa khoảng trắng
        cleaned_text = re.sub(r'\s+', ' ', text).strip()

        return cleaned_text