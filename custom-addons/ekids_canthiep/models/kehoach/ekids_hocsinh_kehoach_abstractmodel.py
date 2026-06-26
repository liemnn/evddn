from odoo import api, fields, models
from datetime import datetime, date, timedelta
from odoo.tools import json  # 🌟 BẮT BUỘC: Sử dụng bộ Json an toàn của Odoo

import logging

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func: {e}")


class HocSinhKeHoachAbstractModel(models.AbstractModel):
    _name = 'ekids.hocsinh_kehoach_abstractmodel'
    _description = 'Kế hoạch can thiệp của học sinh'
    _abstract = True

    def get_owl_canthiep_data(self):
        self.ensure_one()
        today = date.today()

        # 1. Lấy kế hoạch đang can thiệp của học sinh (Giai đoạn trạng thái = '1')
        trangthais = [kehoach_util.KEHOACH_DANG_CANTHIEP]  # '1'
        kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai_ngay(self, self, trangthais, today)

        if not kehoach:
            return {
                'status': 'error',
                'message': 'Không tìm thấy kế hoạch ở trạng thái Đang can thiệp cho học sinh này.'
            }

        # Đóng gói dữ liệu đối tượng kế hoạch tổng quát

        kehoach_obj = {
            'hocsinh': self.name,
            'trangthai': str(kehoach.trangthai),  # Ép chuỗi trạng thái kế hoạch gốc ('1')
            'is_kiemduyet':kehoach.is_kiemduyet,
            'tu_ngay': kehoach.tu_ngay.strftime('%d/%m/%Y') if kehoach.tu_ngay else '',
            'den_ngay': kehoach.den_ngay.strftime('%d/%m/%Y') if kehoach.den_ngay else '',
            'songay': f"{kehoach.songay} ngày" if kehoach.songay else '31 ngày',
            'gv_lap': kehoach.gv_lapkehoach_id.name or 'Chưa phân công',
            'gv_canthiep': kehoach.gv_canthiep_id.name or 'Chưa phân công',
            'gv_chuyenmon': kehoach.gv_kiemduyet_id.name or 'Chưa phân công'

        }

        # Tính toán dải ngày thực tế theo lịch trình của kế hoạch
        start_date = kehoach.tu_ngay
        end_date = kehoach.den_ngay

        timeline_dates = []
        if start_date and end_date:
            curr_date = start_date
            while curr_date <= end_date:
                timeline_dates.append(curr_date)
                curr_date += timedelta(days=1)

        linhvucs_json = []
        linhvucs = kehoach.kehoach_linhvuc_ids
        linhvucs = linhvucs.sorted(key=lambda m: (m.sequence, m.id))

        if linhvucs:
            for linhvuc in linhvucs:
                linhvuc_json = {
                    "id": linhvuc.id,
                    "linhvuc": linhvuc.linhvuc_id.name if linhvuc.linhvuc_id else '',
                    "tuoi": linhvuc.tuoi_id.name if linhvuc.tuoi_id else 'Mọi độ tuổi',
                    "trangthai": "0",
                }

                muctieus_json_list = []
                muctieus = linhvuc.kehoach_muctieu_ids
                muctieus = muctieus.sorted(key=lambda m: (m.sequence, m.id))

                if muctieus:
                    index = 1
                    for muctieu in muctieus:
                        tong_canthiep = muctieu.ketqua_dat + muctieu.ketqua_hinhthanh + muctieu.ketqua_khongdat
                        tyle =muctieu.func_ketqua_tyle_canthiep()
                        tong_str = str(tong_canthiep)+"/"+str(len(muctieu.ketqua2muctieu_ids)) +" (Đạt "+str(tyle)+"% )"
                        muctieu._compute_trangthai()

                        # HIỆU NĂNG CAO: Chỉ tính toán dải ô vuông lịch biểu nếu mục tiêu đã có điểm can thiệp
                        history_days = []
                        if muctieu.trangthai and muctieu.trangthai != '0':
                            existing_results = {kq.ngay: kq for kq in muctieu.ketqua2muctieu_ids if kq.ngay}
                            day_seq = 1
                            for d in timeline_dates:
                                day_data = {
                                    "day_num": day_seq,
                                    "symbol": "",
                                    "status_class": "day-no-study"
                                }
                                if d in existing_results:
                                    res_record = existing_results[d]
                                    if res_record.trangthai == '1':
                                        day_data["symbol"] = "+"
                                        day_data["status_class"] = "day-status-ok"
                                    elif res_record.trangthai == '0':
                                        day_data["symbol"] = "+/-"
                                        day_data["status_class"] = "day-status-half"
                                    elif res_record.trangthai == '-1':
                                        day_data["symbol"] = "-"
                                        day_data["status_class"] = "day-status-fail"
                                history_days.append(day_data)
                                day_seq += 1

                        # Đọc trường kiểm duyệt chuyên môn gốc từ Model ('0', '1', '-1')
                        trangthai_kiemduyet = getattr(muctieu, 'trangthai_kiemduyet', '0')
                        ketqua_dat_lientiep = muctieu.func_ketqua_dat_lientiep()

                        muctieu_json = {
                            "id": muctieu.id,
                            "index": index,
                            "name": muctieu.name or '',
                            "trangthai": str(muctieu.trangthai),  # Trạng thái học tập của mục tiêu
                            "trangthai_kiemduyet": str(trangthai_kiemduyet),  # Trạng thái duyệt của chuyên môn
                            "chucnang": muctieu.muctieu_id.chucnang or '',
                            "thietke": muctieu.muctieu_id.thietke or '',
                            "tieuchi_dat": getattr(muctieu, 'tieuchi_dat', ''),
                            "tieuchi_hinhthanh": getattr(muctieu, 'tieuchi_hinhthanh', ''),
                            "tieuchi_chuadat": getattr(muctieu, 'tieuchi_chuadat', ''),
                            "dat_lientiep": str(ketqua_dat_lientiep),
                            "cnt_all": tong_str,
                            "cnt_ok": str(muctieu.ketqua_dat),
                            "cnt_half": str(muctieu.ketqua_hinhthanh),
                            "cnt_fail": str(muctieu.ketqua_khongdat),
                            "history_days": history_days
                        }
                        muctieus_json_list.append(muctieu_json)
                        index += 1

                linhvuc_json["muctieus"] = muctieus_json_list
                linhvucs_json.append(linhvuc_json)

        return {
            'status': 'success',
            'kehoach': kehoach_obj,
            'linhvucs': linhvucs_json,
        }