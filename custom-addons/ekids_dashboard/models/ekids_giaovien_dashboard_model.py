# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import date, timedelta
import calendar
import logging

_logger = logging.getLogger(__name__)


class GiaovienDashboard(models.AbstractModel):
    _name = 'ekids.dashboard_giaovien'
    _description = 'Dashboard Cá nhân Giáo viên Can thiệp'

    def _xacdinh_nam_taichinh(self, nam_thucte, thang_thucte):
        return nam_thucte - 1 if thang_thucte == 1 else nam_thucte

    def _ds_thang_cua_nam_taichinh(self, nam_taichinh):
        ds = [(nam_taichinh, m) for m in range(2, 13)]
        ds.append((nam_taichinh + 1, 1))
        return ds

    def _lamtron_nghin(self, sotien):
        return int(round((sotien or 0.0) / 1000.0)) * 1000

    def _dinhdang_vnd(self, sotien, co_donvi=True):
        chuoi = f"{self._lamtron_nghin(sotien):,}"
        return f"{chuoi} vnđ" if co_donvi else chuoi

    def _dinhdang_trieu_bieudo(self, sotien):
        val_tr = round((sotien or 0.0) / 1_000_000.0, 1)
        if val_tr == 0:
            val_tr = 0.0
        return f"{val_tr:,.1f}".replace('.', ',') + "tr"

    def _tim_giaovien_hientai(self, giaovien_id=None):
        """Tìm bản ghi ekids.giaovien theo user đăng nhập (hoặc giáo viên đầu tiên nếu Admin xem thử)"""
        if 'ekids.giaovien' not in self.env:
            return False
        gv_model = self.env['ekids.giaovien'].sudo()
        if giaovien_id:
            return gv_model.browse(int(giaovien_id)).exists()

        user = self.env.user
        if 'user_id' in gv_model._fields:
            gv = gv_model.search([('user_id', '=', user.id)], limit=1)
            if gv:
                return gv
        if user.has_group('base.group_system'):
            return gv_model.search([('trangthai', '=', '1')], limit=1) or gv_model.search([], limit=1)
        return False

    @api.model
    def get_dashboard_data(self, month_str=None, giaovien_id=None):
        today = fields.Date.context_today(self)
        gv = self._tim_giaovien_hientai(giaovien_id)

        if not gv:
            return {'has_teacher': False}

        ntc_hientai = self._xacdinh_nam_taichinh(today.year, today.month)
        ds_cap_thang = self._ds_thang_cua_nam_taichinh(ntc_hientai)

        # Danh sách 12 tháng trong năm tài chính hiện tại
        months_options = []
        current_ym = today.strftime('%Y-%m')
        for y_val, m_val in ds_cap_thang:
            val = f"{y_val}-{m_val:02d}"
            lbl = f"Tháng {m_val:02d}/{y_val}" + (" (Tháng này)" if val == current_ym else "")
            months_options.append({'value': val, 'label': lbl})

        valid_months = [m['value'] for m in months_options]
        if not month_str or month_str not in valid_months:
            month_str = current_ym

        nam, thang = map(int, month_str.split('-'))
        ngay_dau_thang = date(nam, thang, 1)
        ngay_20_thang = date(nam, thang, 20)
        ngay_cuoi_thang = date(nam, thang, calendar.monthrange(nam, thang)[1])
        ngay_xet = today if (nam == today.year and thang == today.month) else ngay_20_thang

        # Tuần hiện tại (Thứ 2 -> Chủ nhật theo today)
        tu_ngay_tuan = today - timedelta(days=today.weekday())
        den_ngay_tuan = tu_ngay_tuan + timedelta(days=6)

        # ---------------------------------------------------------------------
        # 1. XÁC ĐỊNH TẬP HỌC SINH PHỤ TRÁCH THEO KẾT LUẬN MỚI NHẤT CỦA TỪNG HỌC SINH:
        #    - Học sinh đang theo học (trangthai = '1')
        #    - Kết luận mới nhất của học sinh đó có trạng thái = '1' (Cho phép lập kế hoạch)
        #      và gv_canthiep_ids chứa giáo viên hiện tại (gv.id)
        # ---------------------------------------------------------------------
        ca_count_map = {}
        if 'ekids.hocsinh_ca_canthiep' in self.env:
            ca_model = self.env['ekids.hocsinh_ca_canthiep'].sudo()
            if 'giaovien_id' in ca_model._fields and 'hocsinh_id' in ca_model._fields:
                for ca in ca_model.search([('giaovien_id', '=', gv.id)]):
                    if ca.hocsinh_id:
                        ca_count_map[ca.hocsinh_id.id] = ca_count_map.get(ca.hocsinh_id.id, 0) + 1

        hs_phutrach_map = {}
        if 'ekids.kehoach_ketluan' in self.env:
            kl_model = self.env['ekids.kehoach_ketluan'].sudo()
            order_str = 'ngay desc, id desc' if 'ngay' in kl_model._fields else (
                'tu_ngay desc, id desc' if 'tu_ngay' in kl_model._fields else 'id desc'
            )
            all_kl_recs = kl_model.search([
                ('hocsinh_id.trangthai', '=', '1'),
            ], order=order_str)

            latest_kl_by_hs = {}
            for kl in all_kl_recs:
                hs = kl.hocsinh_id
                if hs and hs.id not in latest_kl_by_hs:
                    latest_kl_by_hs[hs.id] = kl

            for hs_id, latest_kl in latest_kl_by_hs.items():
                if str(latest_kl.trangthai or '') == '1' and gv.id in latest_kl.gv_canthiep_ids.ids:
                    hs_phutrach_map[hs_id] = {
                        'id': hs_id,
                        'name': latest_kl.hocsinh_id.name,
                        'so_ca': ca_count_map.get(hs_id, 0),
                    }

        # ---------------------------------------------------------------------
        # 2. KẾ HOẠCH ĐÃ LẬP (MỌI TRẠNG THÁI) GIAO KHOẢNG MÙNG 01 -> 20 CỦA THÁNG
        # ---------------------------------------------------------------------
        kh_model = self.env['ekids.kehoach'].sudo()
        kh_thang_recs = kh_model.search([
            ('hocsinh_id', 'in', list(hs_phutrach_map.keys())),
            ('tu_ngay', '<=', ngay_20_thang),
            ('den_ngay', '>=', ngay_dau_thang),
        ], order='hocsinh_id asc, id asc') if hs_phutrach_map else kh_model.browse()

        hs_ids_da_lap_kh = set()
        kh_dang_canthiep = 0
        kh_soan_cho_duyet = 0
        kh_sap_hethan = 0
        ngay_sap_hethan = ngay_xet + timedelta(days=10)

        for kh in kh_thang_recs:
            if kh.hocsinh_id:
                hs_ids_da_lap_kh.add(kh.hocsinh_id.id)
            tt = str(kh.trangthai or '')
            if tt == '1':
                kh_dang_canthiep += 1
                if kh.den_ngay and ngay_xet <= kh.den_ngay <= ngay_sap_hethan:
                    kh_sap_hethan += 1
            elif tt in ('0', '2'):
                kh_soan_cho_duyet += 1

        tong_hs_phutrach = len(hs_phutrach_map)
        hs_da_co_kh = len(hs_ids_da_lap_kh)
        hs_chua_co_kh = max(0, tong_hs_phutrach - hs_da_co_kh)
        tyle_lap_kh = round(hs_da_co_kh / tong_hs_phutrach * 100, 1) if tong_hs_phutrach else 0

        # ---------------------------------------------------------------------
        # 3. DANH SÁCH TRẺ PHỤ TRÁCH & CẬP NHẬT TUẦN (CHỈ KẾ HOẠCH ĐANG CAN THIỆP '1')
        # ---------------------------------------------------------------------
        kh_canthiep_recs = kh_thang_recs.filtered(lambda k: str(k.trangthai or '') == '1')

        last_update_map = {}
        if kh_canthiep_recs:
            kq_groups = self.env['ekids.kehoach_ketqua2muctieu'].sudo()._read_group(
                domain=[
                    ('kehoach_muctieu_id.kehoach_linhvuc_id.kehoach_id', 'in', kh_canthiep_recs.ids),
                    ('ngay', '>=', tu_ngay_tuan),
                    ('ngay', '<=', den_ngay_tuan),
                    '|',
                    ('is_giaovien_capnhat', '=', True),
                    ('trangthai', 'in', ['0', '1', '2']),
                ],
                groupby=['kehoach_muctieu_id'],
                aggregates=['ngay:max'],
            )
            for muctieu, max_ngay in kq_groups:
                if muctieu and max_ngay:
                    kh_id = muctieu.kehoach_linhvuc_id.kehoach_id.id
                    if kh_id not in last_update_map or max_ngay > last_update_map[kh_id]:
                        last_update_map[kh_id] = max_ngay

        kh_canthiep_by_hs = {}
        done_plans = 0
        pending_plans = 0

        for kh in kh_canthiep_recs:
            hs_id = kh.hocsinh_id.id
            last_dt = last_update_map.get(kh.id)
            is_done = bool(last_dt)
            if is_done:
                done_plans += 1
            else:
                pending_plans += 1

            kh_canthiep_by_hs.setdefault(hs_id, []).append({
                'plan_id': kh.id,
                'plan_name': kh.name or f"Kế hoạch T{thang:02d}/{nam}",
                'is_done': is_done,
                'last_date': last_dt.strftime('%d/%m/%Y') if last_dt else '',
            })

        student_rows = []
        for hs_info in sorted(hs_phutrach_map.values(), key=lambda x: x['name'] or ''):
            hs_id = hs_info['id']
            active_plans = kh_canthiep_by_hs.get(hs_id, [])
            if active_plans:
                for p in active_plans:
                    student_rows.append({
                        'student_id': hs_id,
                        'student_name': hs_info['name'],
                        'so_ca': hs_info['so_ca'],
                        'plan_id': p['plan_id'],
                        'plan_name': p['plan_name'],
                        'status': 'done' if p['is_done'] else 'pending',
                        'last_date': p['last_date'],
                    })
            elif hs_id not in hs_ids_da_lap_kh:
                student_rows.append({
                    'student_id': hs_id,
                    'student_name': hs_info['name'],
                    'so_ca': hs_info['so_ca'],
                    'plan_id': False,
                    'plan_name': '',
                    'status': 'no_plan',
                    'last_date': '',
                })

        for idx, row in enumerate(student_rows, start=1):
            row['stt'] = idx

        tong_kh_tuan = done_plans + pending_plans
        tyle_cham_tuan = round(done_plans / tong_kh_tuan * 100) if tong_kh_tuan else 0

        # ---------------------------------------------------------------------
        # 4. CHUYÊN CẦN & NGHỈ PHÉP TRONG THÁNG
        # ---------------------------------------------------------------------
        ngay_nghi_phep = 0.0
        buoi_vang_mat = 0.0
        co_bang_chamcong = False

        if 'ekids.chamcong_giaovien2thang' in self.env:
            cc_rec = self.env['ekids.chamcong_giaovien2thang'].sudo().search([
                ('giaovien_id', '=', gv.id),
                ('chamcong_loai2thang_id.nam', '=', str(nam)),
                ('chamcong_loai2thang_id.thang', '=', str(thang)),
            ], limit=1)
            if cc_rec:
                co_bang_chamcong = True
                ngay_nghi_phep = cc_rec.tong_nghiphep or 0.0
                buoi_vang_mat = (cc_rec.tong_nghi_cangay or 0) + ((cc_rec.tong_dilam_nuabuoi or 0) * 0.5)

        if not co_bang_chamcong and 'ekids.giaovien_nghiphep' in self.env:
            np_recs = self.env['ekids.giaovien_nghiphep'].sudo().search([
                ('giaovien_id', '=', gv.id),
                ('tu_ngay', '<=', ngay_cuoi_thang),
                ('den_ngay', '>=', ngay_dau_thang),
            ])
            for np in np_recs:
                d_start = max(np.tu_ngay, ngay_dau_thang)
                d_end = min(np.den_ngay, ngay_cuoi_thang)
                so_ngay = float((d_end - d_start).days + 1)
                if np.loai == '0':
                    ngay_nghi_phep += so_ngay
                else:
                    buoi_vang_mat += so_ngay

        # ---------------------------------------------------------------------
        # 5. LƯƠNG THỰC LĨNH & THƯỞNG (Từ ekids.luong: field 'luong' & 'tong_thuong')
        # ---------------------------------------------------------------------
        luong_thang_nay = 0.0
        thuong_thang_nay = 0.0
        chart_labels, chart_vals, chart_tr_labels, chart_full_labels = [], [], [], []

        if 'ekids.luong' in self.env:
            luong_model = self.env['ekids.luong'].sudo()

            for y_m, m_val in ds_cap_thang:
                if (y_m, m_val) > (today.year, today.month):
                    break

                rec_l = luong_model.search([
                    ('giaovien_id', '=', gv.id),
                    ('thang_id.nam_id.name', '=', str(y_m)),
                    ('thang_id.name', '=', str(m_val)),
                ], limit=1)

                val_vnd_chan = self._lamtron_nghin(rec_l.luong if rec_l else 0.0)

                if y_m == nam and m_val == thang:
                    luong_thang_nay = val_vnd_chan
                    thuong_thang_nay = self._lamtron_nghin(rec_l.tong_thuong if rec_l else 0.0)

                chart_labels.append(f"T{m_val}")
                chart_vals.append(val_vnd_chan)
                chart_tr_labels.append(self._dinhdang_trieu_bieudo(val_vnd_chan))
                chart_full_labels.append(self._dinhdang_vnd(val_vnd_chan))

        # Lấy ảnh avatar thực tế của giáo viên (ưu tiên trên ekids.giaovien, fallback sang user_id)
        avatar_b64 = False
        for fname in ('image_128', 'avatar_128', 'image_1920', 'image'):
            if fname in gv._fields and getattr(gv, fname, False):
                val = getattr(gv, fname)
                avatar_b64 = val.decode('utf-8') if isinstance(val, bytes) else str(val)
                break

        if not avatar_b64 and getattr(gv, 'user_id', False):
            u_rec = gv.user_id.sudo()
            for fname in ('avatar_128', 'image_128'):
                if fname in u_rec._fields and getattr(u_rec, fname, False):
                    val = getattr(u_rec, fname)
                    avatar_b64 = val.decode('utf-8') if isinstance(val, bytes) else str(val)
                    break

        return {
            'has_teacher': True,
            'teacher': {
                'id': gv.id,
                'name': gv.name or '',
                'avatar_b64': avatar_b64,
                'coso_name': gv.coso_id.name if getattr(gv, 'coso_id', False) else '',
                'tuan_str': f"{tu_ngay_tuan.strftime('%d/%m/%Y')} – {den_ngay_tuan.strftime('%d/%m/%Y')}",
            },
            'months_options': months_options,
            'selected_month': month_str,
            'thang': thang,
            'nam': nam,
            'kpi': {
                'tong_hs': tong_hs_phutrach,
                'hs_da_co_kh': hs_da_co_kh,
                'hs_chua_co_kh': hs_chua_co_kh,
                'tyle_lap_kh': tyle_lap_kh,
                'done_plans': done_plans,
                'pending_plans': pending_plans,
                'tong_kh_tuan': tong_kh_tuan,
                'tyle_cham_tuan': tyle_cham_tuan,
                'ngay_nghi_phep': round(ngay_nghi_phep, 1),
                'buoi_vang_mat': round(buoi_vang_mat, 1),
                'luong_thuclinh_str': self._dinhdang_vnd(luong_thang_nay, co_donvi=False),
                'phucap_str': self._dinhdang_vnd(thuong_thang_nay),
            },
            'ops': {
                'dang_canthiep': kh_dang_canthiep,
                'soan_cho_duyet': kh_soan_cho_duyet,
                'sap_hethan': kh_sap_hethan,
                'chua_co_kh': hs_chua_co_kh,
            },
            'salary_chart': {
                'labels': chart_labels,
                'values': chart_vals,
                'tr_labels': chart_tr_labels,
                'full_labels': chart_full_labels,
            },
            'student_rows': student_rows,
        }