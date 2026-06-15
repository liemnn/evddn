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

        # 1. Lấy kế hoạch đang can thiệp của học sinh
        trangthai = [kehoach_util.KEHOACH_DANG_CANTHIEP]
        kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self, self, trangthai)

        if not kehoach:
            return {
                'status': 'error',
                'message': 'Không tìm thấy kế hoạch ở trạng thái Đang can thiệp cho học sinh này.'
            }

        # GIỮ NGUYÊN cấu trúc key 'kehoach_obj' của anh
        kehoach_obj = {
            'hocsinh': self.name,  # Tên học sinh từ model ekids.hocsinh hiện tại
            'tu_ngay': kehoach.tu_ngay.strftime('%d/%m/%Y') if kehoach.tu_ngay else '',
            'den_ngay': kehoach.den_ngay.strftime('%d/%m/%Y') if kehoach.den_ngay else '',
            'songay': f"{kehoach.songay} ngày" if kehoach.songay else '30 ngày'
        }

        linhvucs_json = []
        linhvucs = kehoach.kehoach_linhvuc_ids

        if linhvucs:
            for linhvuc in linhvucs:
                # GIỮ NGUYÊN cấu trúc key 'linhvuc_json' của anh
                linhvuc_json = {
                    "id": linhvuc.id,
                    "linhvuc": linhvuc.linhvuc_id.name if linhvuc.linhvuc_id else '',
                    "tuoi": linhvuc.tuoi_id.name if linhvuc.tuoi_id else 'Mọi độ tuổi',
                    "trangthai": "0",
                }

                # 🌟 SỬA LỖI: Khởi tạo mảng chứa danh sách mục tiêu để tránh bị ghi đè dữ liệu
                muctieus_json_list = []
                muctieus = linhvuc.kehoach_muctieu_ids

                if muctieus:
                    for muctieu in muctieus:
                        # Đóng gói từng cấu trúc mục tiêu con
                        muctieu_json = {
                            "id": muctieu.id,
                            "index": getattr(muctieu, 'sequence', 1),
                            "name": muctieu.name or '',
                            "trangthai": muctieu.trangthai,

                            # 💡 BỔ SUNG SẴN: Các trường lâm sàng (Đề phòng sau này XML của anh cần gọi ra dùng)
                            "chucnang": muctieu.muctieu_id.chucnang,
                            "thietke": muctieu.muctieu_id.thietke,
                            "tieuchi_dat": getattr(muctieu, 'tieuchi_dat', ''),
                            "tieuchi_hinhthanh": getattr(muctieu, 'tieuchi_hinhthanh', ''),
                            "tieuchi_chuadat": getattr(muctieu, 'tieuchi_chuadat', ''),
                            "cnt_all": "12/30",
                            "cnt_ok": "12",
                            "cnt_half": "15",
                            "cnt_fail": "3"
                        }
                        # Thêm mục tiêu vào danh sách mảng
                        muctieus_json_list.append(muctieu_json)

                # 🌟 ĐỒNG BỘ: Gán mảng danh sách trọn vẹn vào key 'muctieus' nằm trong lĩnh vực
                linhvuc_json["muctieus"] = muctieus_json_list
                linhvucs_json.append(linhvuc_json)

        # GIỮ NGUYÊN cấu trúc đầu ra gốc 100% theo đúng ý anh để map với XML sau này
        return {
            'status': 'success',
            'kehoach': kehoach_obj,
            'linhvucs': linhvucs_json,
        }
