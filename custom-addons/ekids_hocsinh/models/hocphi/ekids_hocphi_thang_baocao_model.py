# -*- coding: utf-8 -*-
from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class HocPhiThangBaoCaoAbstractModel(models.AbstractModel):
    _name = 'report.ekids_hocsinh.hocphi_thang_baocao_template'
    _description = 'Báo cáo học phí động theo danh mục từ chi tiết học phí tháng'

    @api.model
    def _get_report_values(self, docids, data=None):
        hocphi_thang_records = self.env['ekids.hocphi_thang'].browse(docids)

        report_data = {
            'thang_label': '',
            'nam_label': '',
            'coso_name': '',
            'dynamic_columns': [],
            'rows': [],
            'totals': {
                'khac': 0.0,
                'giam_thang_truoc': 0.0,
                'giam_chinh_sach': 0.0,
                'tong_phai_dong': 0.0,
            },
        }

        if hocphi_thang_records:
            thang_rec = hocphi_thang_records[0]
            coso_name = thang_rec.coso_id.name if thang_rec.coso_id else ''
            thang_label = dict(thang_rec._fields['name'].selection).get(thang_rec.name, thang_rec.name) if hasattr(
                thang_rec, 'name') else ''
            nam_label = thang_rec.nam_id.name if thang_rec.nam_id else ''

            # Lấy danh sách cột động
            domain_dm = [('trangthai', '=', '1')]
            if thang_rec.coso_id:
                domain_dm.append(('coso_id', '=', thang_rec.coso_id.id))
            dm_hocphi = self.env['ekids.hocphi_dm'].search(domain_dm, order='sequence asc')

            dynamic_columns = [{'id': dm.id, 'name': dm.name} for dm in dm_hocphi]

            totals = {str(dm.id): 0.0 for dm in dm_hocphi}
            totals.update({
                'khac': 0.0,
                'giam_thang_truoc': 0.0,
                'giam_chinh_sach': 0.0,
                'tong_phai_dong': 0.0
            })

            rows = []
            stt = 1
            for hp in thang_rec.hocphi_ids:
                hs_name = hp.hocsinh_id.name if hp.hocsinh_id else "Không xác định"
                col_amounts = {}
                tien_khac = 0.0

                # 1. Tính tiền cho các cột động hocphi_dm
                for dm in dm_hocphi:
                    tien_dm = 0.0
                    for ca in hp.hocphi_ca_ids:
                        if ca.dm_ca_id and ca.dm_ca_id.dm_hocphi_id == dm:
                            tien_dm += ca.tien or 0.0
                    for bt in hp.hocphi_bantru_ids:
                        if bt.dm_thu_bantru_id and bt.dm_thu_bantru_id.dm_hocphi_id == dm:
                            tien_dm += bt.tien or 0.0

                    col_amounts[str(dm.id)] = tien_dm
                    totals[str(dm.id)] += tien_dm

                # 2. Tính tiền các khoản KHÔNG thuộc hocphi_dm nào (Cộng dồn vào cột Khác)
                for ca in hp.hocphi_ca_ids:
                    if not ca.dm_ca_id or not ca.dm_ca_id.dm_hocphi_id:
                        tien_khac += ca.tien or 0.0

                for bt in hp.hocphi_bantru_ids:
                    if not bt.dm_thu_bantru_id or not bt.dm_thu_bantru_id.dm_hocphi_id:
                        tien_khac += bt.tien or 0.0

                totals['khac'] += tien_khac

                giam_thang_truoc = hp.tien_duoctru or 0.0
                giam_chinh_sach = hp.hocphi_giam or 0.0
                tong_phai_dong = hp.hocphi_phaidong or 0.0

                totals['giam_thang_truoc'] += giam_thang_truoc
                totals['giam_chinh_sach'] += giam_chinh_sach
                totals['tong_phai_dong'] += tong_phai_dong

                rows.append({
                    'stt': stt,
                    'hocsinh_name': hs_name,
                    'col_amounts': col_amounts,
                    'tien_khac': tien_khac,
                    'giam_thang_truoc': giam_thang_truoc,
                    'giam_chinh_sach': giam_chinh_sach,
                    'tong_phai_dong': tong_phai_dong,
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
            'doc_model': 'ekids.hocphi_thang',
            'docs': hocphi_thang_records,
            'data': report_data,
        }