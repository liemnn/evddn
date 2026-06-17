from odoo import api, fields, models
from datetime import datetime,date, timedelta
from odoo.tools import json  # 🌟 BẮT BUỘC: Sử dụng bộ Json an toàn của Odoo

import logging
_logger = logging.getLogger(__name__)


try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")




class HocSinhKeHoachAbstractModel(models.AbstractModel):
    _name = 'ekids.hocsinh_kehoach_abstractmodel'
    _description = 'Kế hoạch can thiệp của học sinh'
    _abstract = True

    def get_owl_canthiep_data(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        date_limit = today - timedelta(days=3)

        # 1. Lấy kế hoạch đang can thiệp của học sinh
        trangthai = [kehoach_util.KEHOACH_DANG_CANTHIEP]
        kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self, self, trangthai)

        if not kehoach:
            return {
                'status': 'error',
                'message': 'Không tìm thấy kế hoạch ở trạng thái Đang can thiệp cho học sinh này.'
            }

        kehoach_obj = {
            'hocsinh': self.name,
            'tu_ngay': kehoach.tu_ngay.strftime('%d/%m/%Y') if kehoach.tu_ngay else '',
            'den_ngay': kehoach.den_ngay.strftime('%d/%m/%Y') if kehoach.den_ngay else '',
            'songay': f"{kehoach.songay} ngày" if kehoach.songay else '30 ngày'
        }

        linhvucs_json = []
        linhvucs = kehoach.kehoach_linhvuc_ids

        if linhvucs:
            # =========================================================================
            # BƯỚC 1: XÁC ĐỊNH MỤC TIÊU ĐƯỢC PHÉP MỞ KHÓA THEO SEQUENCE
            # =========================================================================
            unlocked_muctieu_ids = []
            muctieu_status_map = {}

            for linhvuc in linhvucs:
                sorted_muctieus = linhvuc.kehoach_muctieu_ids.sorted(key=lambda m: (m.sequence, m.id))

                can_open_next = True
                for muctieu in sorted_muctieus:
                    if can_open_next:
                        muctieu_status_map[muctieu.id] = True
                        unlocked_muctieu_ids.append(muctieu.id)

                        # Nếu mục tiêu hiện tại chưa hoàn thành (khác trạng thái '1' - Đạt)
                        # Thì dừng luồng mở khóa, các mục tiêu xếp sau sequence này sẽ bị đóng
                        if muctieu.trangthai != '1':
                            can_open_next = False
                    else:
                        muctieu_status_map[muctieu.id] = False

            # =========================================================================
            # BƯỚC 2: TÍNH TOÁN SỐ LIỆU SỐ CA DẠY TRÊN RAM (CHỈ DÀNH CHO MỤC TIÊU ĐÃ MỞ)
            # =========================================================================
            stats_cache = {}
            if unlocked_muctieu_ids:
                all_sessions = self.env['ekids.kehoach_ketqua2muctieu'].search_read([
                    ('kehoach_muctieu_id', 'in', unlocked_muctieu_ids)
                ], ['kehoach_muctieu_id', 'ngay', 'ketqua'])

                for session in all_sessions:
                    m_id = session['kehoach_muctieu_id'][0]
                    s_date = fields.Date.to_date(session['ngay'])
                    res_val = str(session.get('ketqua') or '')

                    if m_id not in stats_cache:
                        stats_cache[m_id] = {'total': 0, 'ok': 0, 'half': 0, 'fail': 0, 'latest_session_date': None}

                    stats_cache[m_id]['total'] += 1
                    if res_val in ['1', 'approved', 'dat']:
                        stats_cache[m_id]['ok'] += 1
                    elif res_val in ['0', 'half', 'hinhthanh']:
                        stats_cache[m_id]['half'] += 1
                    elif res_val in ['-1', 'fail', 'chuadat']:
                        stats_cache[m_id]['fail'] += 1

                    # Lưu vết ngày ghi nhận gần nhất
                    if not stats_cache[m_id]['latest_session_date'] or s_date > stats_cache[m_id][
                        'latest_session_date']:
                        stats_cache[m_id]['latest_session_date'] = s_date

            # =========================================================================
            # BƯỚC 3: ĐÓNG GÓI DỮ LIỆU ĐẦU RA CHUẨN UX MỚI
            # =========================================================================
            for linhvuc in linhvucs:
                linhvuc_json = {
                    "id": linhvuc.id,
                    "linhvuc": linhvuc.linhvuc_id.name if linhvuc.linhvuc_id else '',
                    "tuoi": linhvuc.tuoi_id.name if linhvuc.tuoi_id else 'Mọi độ tuổi',
                    "trangthai": "0",
                }

                muctieus_json_list = []
                sorted_muctieus = linhvuc.kehoach_muctieu_ids.sorted(key=lambda m: (m.sequence, m.id))

                for muctieu in sorted_muctieus:
                    is_unlocked = muctieu_status_map.get(muctieu.id, False)

                    cnt_all, cnt_ok, cnt_half, cnt_fail = "0", "0", "0", "0"

                    # 🌟 ĐỊNH NGHĨA QUY TẮC PHÂN LOẠI TRẠNG THÁI MỚI THEO Ý ANH LIÊM
                    if muctieu.trangthai == '1':
                        status_text = "Đạt"
                        status_class = "status-pill-1"  # Màu Xanh Lá
                    elif is_unlocked:
                        status_text = "Đang can thiệp"
                        status_class = "status-pill-0"  # Màu Vàng Cam tươi sáng
                    else:
                        status_text = "Chưa can thiệp"
                        status_class = "status-pill-locked"  # Màu Xám Slate

                    # 🌟 ĐỊNH NGHĨA QUY TẮC KHÓA BẤM NÚT 3 NGÀY
                    allow_update = False
                    if is_unlocked:
                        # 1. Nếu là mục tiêu đang can thiệp dở dang -> Luôn cho phép bấm nút Can thiệp
                        if muctieu.trangthai != '1':
                            allow_update = True
                        # 2. Nếu đã Đạt -> Chỉ cho sửa nếu ngày có ca dạy gần nhất nằm trong khoảng 3 ngày đổ lại
                        else:
                            m_stats = stats_cache.get(muctieu.id)
                            if m_stats and m_stats['latest_session_date'] and m_stats[
                                'latest_session_date'] >= date_limit:
                                allow_update = True

                    # Đổ dữ liệu thống kê thật nếu mục tiêu đã mở
                    if is_unlocked and muctieu.id in stats_cache:
                        m_stats = stats_cache[muctieu.id]
                        cnt_ok = str(m_stats['ok'])
                        cnt_half = str(m_stats['half'])
                        cnt_fail = str(m_stats['fail'])
                        cnt_all = f"{cnt_ok}/{m_stats['total']}"

                    muctieu_json = {
                        "id": muctieu.id,
                        "index": getattr(muctieu, 'sequence', 1),
                        "name": muctieu.name or '',
                        "trangthai": muctieu.trangthai,
                        "chucnang": muctieu.muctieu_id.chucnang,
                        "thietke": muctieu.muctieu_id.thietke,
                        "tieuchi_dat": getattr(muctieu, 'tieuchi_dat', ''),
                        "tieuchi_hinhthanh": getattr(muctieu, 'tieuchi_hinhthanh', ''),
                        "tieuchi_chuadat": getattr(muctieu, 'tieuchi_chuadat', ''),
                        "cnt_all": cnt_all,
                        "cnt_ok": cnt_ok,
                        "cnt_half": cnt_half,
                        "cnt_fail": cnt_fail,

                        # Hai trường kiểm soát giao diện XML
                        "status_text": status_text,
                        "status_class": status_class,
                        "is_unlocked": is_unlocked,
                        "allow_update": allow_update
                    }
                    muctieus_json_list.append(muctieu_json)

                linhvuc_json["muctieus"] = muctieus_json_list
                linhvucs_json.append(linhvuc_json)

        return {
            'status': 'success',
            'kehoach': kehoach_obj,
            'linhvucs': linhvucs_json,
        }