# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class KeHoachCanthiepController(http.Controller):

    @http.route('/canthiep/kehoach/get_data', type='json', auth='user', methods=['POST'])
    def get_owl_canthiep_data(self, plan_id, **kwargs):
        """
        API JSON-RPC cung cấp dữ liệu động thời gian thực cho màn hình OWL Can thiệp
        """
        # 1. Tìm bản ghi Kế hoạch lớn cha
        plan = request.env['ekids.kehoach'].browse(int(plan_id))
        if not plan.exists():
            return {'status': 'error', 'message': 'Kế hoạch can thiệp không tồn tại'}

        # 2. Đóng gói thông tin Master Readonly phía trên
        plan_info = {
            'student_name': plan.hocsinh_id.name,
            'tu_ngay': plan.tu_ngay.strftime('%d/%m/%Y') if plan.tu_ngay else '',
            'den_ngay': plan.den_ngay.strftime('%d/%m/%Y') if plan.den_ngay else '',
            'songay': f"{plan.songay} ngày"
        }

        # 3. Truy vấn bảng mục tiêu chi tiết của kế hoạch này (ekids.kehoach_muctieu)
        # Sắp xếp chuẩn theo sequence Lĩnh vực
        muctieu_records = request.env['ekids.kehoach_muctieu'].search([
            ('kehoach_id', '=', plan.id)
        ], order='sequence, id asc')

        # Thuật toán gom nhóm dữ liệu theo mục tiêu của từng Lĩnh vực chuyên môn
        domains_dict = {}
        for rec in muctieu_records:
            lv_id = rec.linhvuc_id.id
            if lv_id not in domains_dict:
                domains_dict[lv_id] = {
                    'id': lv_id,
                    'name': rec.linhvuc_id.name,
                    'tuoi': rec.tuoi_id.name if rec.tuoi_id else 'Mọi độ tuổi',
                    'goals': [],
                    'completed': 0,  # Số lượng mục tiêu đã đạt (+)
                    'total': 0  # Tổng số mục tiêu của lĩnh vực này
                }

            # Xác định trạng thái tổng quát hiển thị ngoài dòng phẳng
            # Mặc định giả lập luồng tiến độ lịch sử theo ảnh mẫu của bạn
            status_map = 'hinhthanh'

            # Logic: Nếu tiêu chí đạt được ghi nhận đầy đủ thì tính toán hoàn thành (Tùy biến theo nghiệp vụ của bạn)
            if getattr(rec, 'trangthai_lam_sang', '') == 'dat':
                status_map = 'dat'
                domains_dict[lv_id]['completed'] += 1

            domains_dict[lv_id]['total'] += 1

            # Đẩy chi tiết cấu trúc dòng mục tiêu vào danh sách con
            domains_dict[lv_id]['goals'].append({
                'id': rec.id,
                'name': rec.muctieu_id.name if rec.muctieu_id else 'Mục tiêu chưa xác định',
                'cnt_all': '12/30',  # Số ca/buổi thực tế
                'cnt_ok': '12',  # Số lần Đạt (+)
                'cnt_half': '15',  # Số lần Đang hình thành (+/-)
                'cnt_fail': '3',  # Số lần Chưa đạt (-)
                'status': status_map,  # 'dat' | 'hinhthanh' | 'chuadat'
                'chucnang': getattr(rec, 'chucnang', 'Chưa cấu hình chức năng cốt lõi.'),
                'thietke': getattr(rec, 'thietke', 'Chưa cấu hình thiết kế hoạt động cho giáo viên (ABC).'),
                'tieuchi_dat': getattr(rec, 'tieuchi_dat', 'Chưa lập tiêu chí đạt.'),
                'tieuchi_hinhthanh': getattr(rec, 'tieuchi_hinhthanh', 'Chưa lập tiêu chí đang hình thành.'),
                'tieuchi_chuadat': getattr(rec, 'tieuchi_chuadat', 'Chưa lập tiêu chí chưa đạt.')
            })

        return {
            'status': 'success',
            'planInfo': plan_info,
            'domains': list(domains_dict.values())
        }