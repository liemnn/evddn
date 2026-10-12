# -*- coding: utf-8 -*-
from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class LuongThangBaoCaoAbstractModel(models.AbstractModel):
    _name = 'report.ekids_giaovien.luong_thang_baocao_template'
    _description = 'Báo cáo Lương động theo danh mục từ chi tiết lương tháng'

    @api.model
    def _get_report_values(self, docids, data=None):
        luong_thang_records = self.env['ekids.luong_thang'].browse(docids)

        report_data = {
            'thang_label': '',
            'nam_label': '',
            'coso_name': '',
            'dynamic_columns': [],
            'rows': [],
            'totals': {
                'thuc_linh': 0.0,
                'nhatruong_thuc_chi': 0.0,
            },
        }

        if luong_thang_records:
            thang_rec = luong_thang_records[0]
            coso_name = thang_rec.coso_id.name if thang_rec.coso_id else ''
            thang_label = dict(thang_rec._fields['name'].selection).get(thang_rec.name, thang_rec.name) if hasattr(
                thang_rec, 'name') else ''
            nam_label = thang_rec.nam_id.name if thang_rec.nam_id else ''

            # Lấy danh sách cột động từ ekids.luong_dm theo cơ sở và trạng thái hoạt động
            domain_dm = [('trangthai', '=', '1')]
            if thang_rec.coso_id:
                domain_dm.append(('coso_id', '=', thang_rec.coso_id.id))

            dm_luongs = self.env['ekids.luong_dm'].search(domain_dm, order='sequence asc')

            dynamic_columns = [{'id': dm.id, 'name': dm.name} for dm in dm_luongs]

            totals = {str(dm.id): 0.0 for dm in dm_luongs}
            totals.update({
                'thuc_linh': 0.0,
                'nhatruong_thuc_chi': 0.0,
            })

            # Lấy danh sách bảng lương chi tiết của giáo viên trong tháng này
            luong_records = self.env['ekids.luong'].search([
                ('thang_id', '=', thang_rec.id),
                ('coso_id', '=', thang_rec.coso_id.id)
            ])

            rows = []
            stt = 1
            for l_rec in luong_records:
                gv_name = l_rec.giaovien_id.name if l_rec.giaovien_id else "Không xác định"
                col_amounts = {}

                # Gộp tất cả các dòng hạng mục lương của giáo viên
                all_hangmucs = l_rec.luong_cong_ids + l_rec.luong_tru_ids + l_rec.nhatruong_chitra_ids + l_rec.luong_thongtin_ids

                # 1. Tính số tiền cho các cột động theo ekids.luong_dm (thông qua liên kết dm_chitra_id.dm_luong_id)[cite: 19, 20]
                for dm in dm_luongs:
                    tien_dm = sum(
                        hm.tien for hm in all_hangmucs if hm.dm_chitra_id and hm.dm_chitra_id.dm_luong_id == dm)
                    col_amounts[str(dm.id)] = tien_dm
                    totals[str(dm.id)] += tien_dm

                # 2. Lấy giá trị Tổng thực lĩnh và Tổng nhà trường thực chi từ model ekids.luong[cite: 10]
                thuc_linh = l_rec.luong or 0.0
                nhatruong_thuc_chi = l_rec.tong_nhatruong_chi or 0.0

                totals['thuc_linh'] += thuc_linh
                totals['nhatruong_thuc_chi'] += nhatruong_thuc_chi

                rows.append({
                    'stt': stt,
                    'giaovien_name': gv_name,
                    'col_amounts': col_amounts,
                    'thuc_linh': thuc_linh,
                    'nhatruong_thuc_chi': nhatruong_thuc_chi,
                })
                stt += 1

            report_data = {
                'thang_label': thang_label,
                'nam_label': nam_label,
                'coso_name': coso_name,
                'dynamic_columns': dynamic_columns,
                'rows': rows,
                'totals': totals,
            }

        return {
            'doc_ids': docids,
            'doc_model': 'ekids.luong_thang',
            'docs': luong_thang_records,
            'data': report_data,
        }