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




class KeHoachCopyAbstractModel(models.AbstractModel):
    _name = 'ekids.kehoach_abstractmodel'
    _description = 'Kế hoạch can thiệp của học sinh'
    _abstract = True

    def func_copy_muctieu_thangtruoc_khongdat_sang(self):

        linhvucs = self.ketluan_id.linhvuc_ids
        if linhvucs:
            #B1: copy Linh vuc
            for linhvuc in linhvucs:
                kehoach_linhvuc = self.env['ekids.kehoach_linhvuc'].search([
                    ("kehoach_id","=",self.id)
                    ,("linhvuc_id","=",linhvuc.linhvuc_id.id)
                    ,("tuoi_id", "=", linhvuc.tuoi_id.id)
                ],limit=1)
                if not kehoach_linhvuc:
                    data = {
                        'sequence': linhvuc.sequence,
                        'kehoach_id': self.id,
                        'chuongtrinh_id': linhvuc.linhvuc_id.chuongtrinh_id.id,
                        'linhvuc_id': linhvuc.linhvuc_id.id,
                        'tuoi_id': linhvuc.tuoi_id.id,
                    }
                    kehoach_linhvuc = self.env['ekids.kehoach_linhvuc'].create(data)

                kehoach_truoc = self.kehoach_truoc_id

                if kehoach_truoc and kehoach_linhvuc:
                    #copy các mục tiêu từ kế hoạch trước sang.
                    kehoach_linhvuc_truoc = self.func_kehoach_linhvuc_truocs(kehoach_linhvuc.linhvuc_id.id,kehoach_linhvuc.tuoi_id.id,kehoach_truoc)
                    if kehoach_linhvuc_truoc:
                        self.func_copy_muctieu_thangtruoc_khongdat_sang_tu_linhvuc(kehoach_linhvuc,kehoach_linhvuc_truoc)

    def func_copy_muctieu_thangtruoc_khongdat_sang_tu_linhvuc(self, kehoach_linhvuc,kehoach_linhvuc_truoc):
        kehoach_muctieu_truocs = kehoach_linhvuc_truoc.kehoach_muctieu_ids
        if kehoach_muctieu_truocs:
            for kehoach_muctieu_truoc in kehoach_muctieu_truocs:
                kehoach_muctieu = self.env['ekids.kehoach_muctieu'].search([
                    ("kehoach_id", "=", kehoach_linhvuc.kehoach_id.id)
                    ,("muctieu_id", "=", kehoach_muctieu_truoc.muctieu_id.id)

                ],limit=1)
                if (kehoach_muctieu_truoc.trangthai_kiemduyet =="1"
                        or kehoach_muctieu_truoc.trangthai_kiemduyet =="-2"):
                    #TH1: kế hoạch tháng trước đã đạt, hoặc hủy bỏ do đánh giá nếu có thì xóa đi
                    if kehoach_muctieu:
                        kehoach_muctieu.unlink()

                else:
                    if not kehoach_muctieu:
                        data ={
                            "sequence": kehoach_muctieu_truoc.muctieu_id.sequence,
                            "kehoach_linhvuc_id":kehoach_linhvuc.id,
                            "kehoach_muctieu_thangtruoc_id": kehoach_muctieu_truoc.id,
                            "muctieu_id": kehoach_muctieu_truoc.muctieu_id.id,
                            "muctieu_them": kehoach_muctieu_truoc.muctieu_them,
                            "ghichu": kehoach_muctieu_truoc.ghichu,
                            "trangthai":"0"
                        }
                        self.env['ekids.kehoach_muctieu'].create(data)



    def func_kehoach_linhvuc_truocs(self,linhvuc_id,tuoi_id,kehoach_truoc):
        kehoach_linhvuc_ids = kehoach_truoc.kehoach_linhvuc_ids
        for kehoach_linhvuc_truoc in kehoach_linhvuc_ids:
            if kehoach_linhvuc_truoc.linhvuc_id.id == linhvuc_id and kehoach_linhvuc_truoc.tuoi_id.id == tuoi_id:
                return kehoach_linhvuc_truoc


