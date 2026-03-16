import os
from bs4 import BeautifulSoup
from datetime import timedelta

from odoo import fields, models, api, _

import calendar
import xlsxwriter
import base64
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


class ChiTieuThangReportWizard(models.Model):
    _name = 'ekids.chitieu_thang_report_wizard'
    _description = 'Báo cáo chi tiêu tháng'

    coso_id = fields.Many2one('ekids.coso', string='Cơ sở', readonly=True)
    nam_id = fields.Many2one('ekids.chitieu_nam', string='Năm')
    thang_id = fields.Selection(
        [('02', 'Tháng 2'), ('03', 'Tháng 3'), ('04', 'Tháng 4'), ('05', 'Tháng 5'),
         ('06', 'Tháng 6'), ('07', 'Tháng 7'), ('08', 'Tháng 8'), ('09', 'Tháng 9'), ('10', 'Tháng 10'),
         ('11', 'Tháng 11'), ('12', 'Tháng 12'), ('01', 'Tháng 1')],
        string='Tháng'
    )
    tong_chitieu = fields.Integer(string='Tổng Chi Tiêu', readonly=True)
    chon_thang_nam = fields.Char(string='Tháng/Năm', readonly=True)
    loaichitieu_html = fields.Html(string='Loại Chi Tiêu', compute='_compute_loaichitieu_html')
    chitieu_hangngay_ids = fields.One2many('ekids.chitieuhangngay', string='Chi Tiêu Hàng Ngày',
                                           compute='_compute_chitieu_hangngay_ids')

    def default_get(self, fields):
        res = super(ChiTieuThangReportWizard, self).default_get(fields)
        context = self.env.context
        record_id = context.get('active_id')
        record = self.env['ekids.chitieuhangthang'].browse(record_id)
        res.update({
            'coso_id': record.coso_id.id,
            'chon_thang_nam': record.chon_thang_nam,
            'tong_chitieu': record.tong,
        })
        return res

    @api.depends('coso_id')
    def _compute_loaichitieu_html(self):
        for record in self:
            if record.coso_id:
                loaichitieu_records = self.env['ekids.loaichitieu'].search([])
                html_content = '<ul>'
                for loaichitieu in loaichitieu_records:
                    total_amount = self.env['ekids.chitieuhangngay'].search(
                        [('coso_id', '=', record.coso_id.id), ('loaichitieu', '=', loaichitieu.id)]).mapped('price')
                    total_amount_sum = sum(total_amount)
                    formatted_amount = "{:,.0f} VNĐ".format(total_amount_sum).replace(",", ".")
                    html_content += f'<li>{loaichitieu.loaichitieu} : {formatted_amount}</li>'
                html_content += '</ul>'
                record.loaichitieu_html = html_content
            else:
                record.loaichitieu_html = '<ul></ul>'

    @api.depends('coso_id', 'chon_thang_nam')
    def _compute_chitieu_hangngay_ids(self):
        for record in self:
            if record.coso_id and record.chon_thang_nam:
                try:
                    thang, nam = record.chon_thang_nam.split('/')
                    thang = int(thang.strip().replace('Tháng ', ''))
                    nam = int(nam.strip())
                    last_day = calendar.monthrange(nam, thang)[1]
                    start_date = f'{nam}-{thang:02}-01'
                    end_date = f'{nam}-{thang:02}-{last_day}'
                    chitieu_records = self.env['ekids.chitieuhangngay'].search([
                        ('coso_id', '=', record.coso_id.id),
                        ('ngaychi', '>=', start_date),
                        ('ngaychi', '<=', end_date)
                    ])
                    record.chitieu_hangngay_ids = chitieu_records
                except ValueError:
                    record.chitieu_hangngay_ids = False
            else:
                record.chitieu_hangngay_ids = False

    def action_export_report(self):
        data = BytesIO()
        workbook = xlsxwriter.Workbook(data)
        sheet = workbook.add_worksheet('Báo Cáo Chi Tiêu')

        # Định nghĩa các cột
        columns = ['Ngày chi', 'Loại chi', 'Số tiền', 'Người chi', 'Ngày nhập liệu', 'Nội dung chi']

        # Ghi tiêu đề các cột
        for col_num, column_title in enumerate(columns):
            sheet.write(0, col_num, column_title)

        # Lấy dữ liệu chi tiêu hàng ngày
        chitieu_records = self.env['ekids.chitieuhangngay'].search([])

        # Ghi dữ liệu vào file Excel
        row = 1
        for record in chitieu_records:
            sheet.write(row, 0, str(record.ngaychi))
            sheet.write(row, 1, record.loaichitieu.loaichitieu)  # Sử dụng record.loaichitieu.loaichitieu
            sheet.write(row, 2, str(record.price))  # Chuyển đổi record.price thành chuỗi
            sheet.write(row, 3, record.user_id)
            sheet.write(row, 4, str(record.ngaynhaplieu))
            sheet.write(row, 5, str(record.desc))
            row += 1

        # Đóng workbook và lưu dữ liệu vào file
        workbook.close()
        data.seek(0)
        report_file = base64.b64encode(data.read())

        # Tạo attachment và trả về action để download file
        attachment = self.env['ir.attachment'].create({
            'name': 'Bao_Cao_Chi_Tieu_Thang.xlsx',
            'datas': report_file,
            'type': 'binary',
            'res_model': 'chitieu.thang.report.wizard',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_export_report_pdf(self):
        data = BytesIO()
        pdf = canvas.Canvas(data, pagesize=A4)
        width, height = A4

        # Đường dẫn tương đối tới file font
        current_dir = os.path.dirname(os.path.abspath(__file__))  # Thư mục hiện tại của file Python
        DejaVuSans_path = os.path.join(current_dir, '..', 'font', 'DejaVuSans.ttf')
        DejaVuSans_Bold_path = os.path.join(current_dir, '..', 'font', 'DejaVuSans-Bold.ttf')

        pdfmetrics.registerFont(TTFont('DejaVuSans', DejaVuSans_path))
        pdfmetrics.registerFont(TTFont('DejaVuSans_Bold', DejaVuSans_Bold_path))

        # Định nghĩa tiêu đề và cột
        title = f"Báo Cáo Chi Tiêu Tháng {self.chon_thang_nam}"
        columns = ['Ngày Chi', 'Loại Chi', 'Số Tiền', 'Người Chi', 'Ngày Nhập Liệu', 'Nội Dung Chi']

        # Vẽ tiêu đề
        pdf.setFont("DejaVuSans_Bold", 16)
        pdf.drawCentredString(width / 2.0, height - 30 * mm, title)

        # Vẽ thông tin cơ sở và tổng chi tiêu
        pdf.setFont("DejaVuSans", 12)
        pdf.drawString(10 * mm, height - 40 * mm, f"Cơ sở: {self.coso_id.name}")
        pdf.drawString(10 * mm, height - 50 * mm, f"Tháng/Năm: {self.chon_thang_nam}")
        pdf.drawString(10 * mm, height - 60 * mm, f"Tổng chi tiêu: {self.tong_chitieu:,} VNĐ".replace(',', '.'))

        # Vẽ các loại chi tiêu
        y_position = height - 80 * mm
        pdf.setFont("DejaVuSans_Bold", 12)
        pdf.drawString(10 * mm, y_position, "Các loại chi tiêu:")
        y_position -= 10 * mm
        pdf.setFont("DejaVuSans", 10)

        # Sử dụng BeautifulSoup để loại bỏ thẻ HTML
        soup = BeautifulSoup(self.loaichitieu_html, "html.parser")
        for line in soup.stripped_strings:
            pdf.drawString(10 * mm, y_position, line)
            y_position -= 10 * mm

        # Vẽ tiêu đề các cột
        y_position -= 10 * mm
        pdf.setFont("DejaVuSans_Bold", 12)
        col_widths = [30 * mm, 40 * mm, 20 * mm, 30 * mm, 40 * mm, 50 * mm]
        for col_num, column_title in enumerate(columns):
            pdf.drawString(sum(col_widths[:col_num]) + 10 * mm, y_position, column_title)

        y_position -= 10 * mm

        # Lấy dữ liệu chi tiêu hàng ngày
        chitieu_records = self.chitieu_hangngay_ids

        # Vẽ dữ liệu vào file PDF
        pdf.setFont("DejaVuSans", 10)
        for record in chitieu_records:
            if y_position < 20 * mm:
                pdf.showPage()
                pdf.setFont("DejaVuSans_Bold", 12)
                for col_num, column_title in enumerate(columns):
                    pdf.drawString(sum(col_widths[:col_num]) + 10 * mm, y_position, column_title)
                y_position = height - 40 * mm
                pdf.setFont("DejaVuSans", 10)

            pdf.drawString(10 * mm, y_position, str(record.ngaychi))
            pdf.drawString(40 * mm, y_position, ', '.join(record.loaichitieu.mapped('loaichitieu')))
            pdf.drawString(80 * mm, y_position, f"{record.price:,}".replace(',', '.'))
            pdf.drawString(100 * mm, y_position,
                           record.user_id or '')  # Sử dụng record.user_id.name nếu user_id là Many2one
            pdf.drawString(130 * mm, y_position, str(record.ngaynhaplieu))
            pdf.drawString(170 * mm, y_position, record.desc.replace('\n', ' '))
            y_position -= 10 * mm

        # Đóng PDF
        pdf.save()
        data.seek(0)
        report_file = base64.b64encode(data.read())

        # Tạo attachment và trả về action để download file
        attachment = self.env['ir.attachment'].create({
            'name': 'Bao_Cao_Chi_Tieu_Thang.pdf',
            'datas': report_file,
            'type': 'binary',
            'res_model': 'your.model.name',
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
