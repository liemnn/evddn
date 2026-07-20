from odoo import models, fields, api, Command
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import html2plaintext
from odoo.osv import expression

import logging

_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import giaovien_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")


class BaoCaoNguonLucWizard(models.TransientModel):
    _name = 'ekids.baocao_nguonluc'
    _description = 'Báo cáo lợi nhuận của cơ sở'

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", readonly=True)

    tu_thang = fields.Selection(
        [('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'),
         ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'),
         ('11', 'Tháng 11'), ('12', 'Tháng 12')],
        string='Tháng', required=True, default='1'
    )

    tu_nam = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year - 20, datetime.now().year + 1)],
        string="Năm", required=True, default=lambda self: str(date.today().year)
    )

    den_thang = fields.Selection(
        [('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'),
         ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'),
         ('11', 'Tháng 11'), ('12', 'Tháng 12')],
        string='Tháng', required=True, default='1'
    )

    den_nam = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year - 20, datetime.now().year + 2)],
        string="Năm", required=True, default=lambda self: str(date.today().year + 1)
    )

    loai = fields.Selection(
        [('1', 'Báo cáo số lượng [Giáo viên/Học sinh]'),
         ('2', 'Báo cáo danh sách Giáo viên'),
         ('3', 'Báo cáo danh sách Học sinh')],
        string='Loại báo cáo', required=True, default='1'
    )

    coso_ids = fields.Many2many('ekids.coso',
                                relation="ekids_baocao_nguonluc_baocao2coso_rel",
                                column1="baocao_nguonluc_id",
                                column2="coso_Id",
                                string="Danh sách Cơ sở", required=True
                                )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get('coso_id') and 'coso_ids' in fields_list:
            res['coso_ids'] = [(6, 0, [res['coso_id']])]
        return res

    def get_table_data(self):
        if self.loai == '1':
            return self.get_table_data_soluong_hocsinh_giaovien()
        elif self.loai == '2':
            return self.get_table_data_danhsach_giaovien()
        else:
            return self.get_table_data_danhsach_hocsinh()

    def get_table_data_danhsach_hocsinh(self):
        table_data = [
            ['TT', 'Họ và tên', 'Giới tính', 'Ngày sinh', 'Tuổi', 'Ngày nhập học', 'Thời gian học', 'Địa chỉ', 'Cơ sở']]
        tu_ngay = date(int(self.tu_nam), int(self.tu_thang), 1)
        ngays = ngay_util.func_get_cacngay_trong_thang(int(self.den_nam), int(self.den_thang))
        den_ngay = ngays[-1]

        hocsinhs = hocsinh_util.func_danhsach_hocsinh_khoang_thoigian(self, self.coso_ids.ids, tu_ngay, den_ngay)
        if hocsinhs:
            index = 1
            for hs in hocsinhs:
                xa = hs.dm_xa_id.name if hs.dm_xa_id else False
                tinh = hs.dm_tinh_id.name if hs.dm_tinh_id else False
                diachi = ", ".join(filter(None, [xa, tinh]))
                gioitinh = "Nam" if hs.gioitinh == '1' else 'Nữ'

                table_data.append([
                    str(index), hs.name, gioitinh, string_util.date2string(hs.ngaysinh),
                    hs.tuoi, string_util.date2string(hs.ngay_nhaphoc), hs.thoigian_hoc, diachi,
                    hs.coso_id.name if hs.coso_id else ''
                ])
                index += 1
        return table_data

    def get_table_data_danhsach_giaovien(self):
        table_data = [
            ['TT', 'Họ và tên', 'Ngày sinh', 'CCCD', 'Nơi cư trú', 'Thâm niên', 'Vị trí công việc', 'Đơn vị công tác']]
        tu_ngay = date(int(self.tu_nam), int(self.tu_thang), 1)
        ngays = ngay_util.func_get_cacngay_trong_thang(int(self.den_nam), int(self.den_thang))
        den_ngay = ngays[-1]

        giaoviens = giaovien_util.func_danhsach_giaovien_khoang_thoigian(self, self.coso_ids.ids, tu_ngay, den_ngay)
        if giaoviens:
            index = 1
            for gv in giaoviens:
                desc = html2plaintext(gv.desc) if gv.desc else ''
                table_data.append([
                    str(index), gv.name, string_util.date2string(gv.ngaysinh), gv.cccd,
                    gv.diachi_cutru, gv.tham_nien, desc, gv.coso_id.name if gv.coso_id else ''
                ])
                index += 1
        return table_data

    def get_table_data_soluong_hocsinh_giaovien(self):
        table_data = [
            ['TT', 'Tháng', 'Năm', '[1] Tổng Học sinh', 'Nghỉ trong tháng', 'Mới trong tháng', '[2] Tổng Giáo viên']]
        ngay_first = date(int(self.tu_nam), int(self.tu_thang), 1)
        ngay_last = date(int(self.den_nam), int(self.den_thang), 1)

        ngay = ngay_first
        sum_data = {'tong': 0, 'nghi': 0, 'moi': 0}
        index = 1
        while ngay <= ngay_last:
            table_data = self.get_table_data_by_thang(table_data, index, ngay.year, ngay.month, sum_data)
            ngay = ngay + relativedelta(months=1)
            index += 1  # Đã sửa lỗi vòng lặp index

        table_data.append([
            '', 'Tổng', '',
            self.number2string(sum_data['tong']),
            self.number2string(sum_data['nghi']),
            self.number2string(sum_data['moi']), ''
        ])
        return table_data

    def get_table_data_by_thang(self, table_data, index, nam, thang, sum_data):
        tong_hs = hocsinh_util.sum_tong_hocsinh_trong_thang(self,self.coso_ids.ids,nam, thang)
        hs_nghi = hocsinh_util.sum_tong_hocsinh_nghi_trong_thang(self,self.coso_ids.ids,nam, thang)
        hs_moi = hocsinh_util.sum_tong_hocsinh_moi_trong_thang(self,self.coso_ids.ids,nam, thang)
        giaovien = giaovien_util.sum_tong_giaovien_trong_thang(self,self.coso_ids.ids,nam, thang)

        table_data.append([
            str(index), 'Tháng ' + str(thang), str(nam),
            self.number2string(tong_hs), self.number2string(hs_nghi),
            self.number2string(hs_moi), self.number2string(giaovien),
        ])
        if sum_data['tong'] <= 0:
            sum_data['tong'] = tong_hs

        sum_data['tong'] = int(sum_data['tong']) + hs_moi - hs_nghi
        sum_data['nghi'] = int(sum_data['nghi']) + hs_nghi
        sum_data['moi'] = int(sum_data['moi']) + hs_moi
        return table_data

    from odoo.osv import expression

    from odoo.osv import expression





    def action_xem_baocao(self):
        return self.env.ref('ekids_baocao.action_report_view_nguonluc').report_action(self)

    def number2string(self, total):
        return "{:,.0f}".format(total)

    def string2number(self, s):
        if not s: return 0
        return float(s.replace(",", "").strip())