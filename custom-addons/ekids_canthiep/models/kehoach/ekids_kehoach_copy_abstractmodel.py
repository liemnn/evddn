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
        #self là kế hoạch
        trangthais = [kehoach_util.KEHOACH_DANG_CANTHIEP,kehoach_util.KEHOACH_HET_HIEULUC]
        kehoach_truoc = kehoach_util.func_get_kehoach_hocsinh_trangthai(self, self.hocsinh_id, trangthais)
        linhvucs = self.ketluan_id.linhvuc_ids
        if linhvucs:
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

                if kehoach_truoc and kehoach_linhvuc:
                    #copy các mục tiêu từ kế hoạch trước sang.
                    linhvuc_truoc = self.func_kehoach_linhvuc_truocs(kehoach_linhvuc.linhvuc_id.id,kehoach_linhvuc.tuoi_id.id,kehoach_truoc)
                    if linhvuc_truoc:
                        self.func_copy_muctieu_thangtruoc_khongdat_sang_tu_linhvuc(kehoach_linhvuc,linhvuc_truoc)

    def func_copy_muctieu_thangtruoc_khongdat_sang_tu_linhvuc(self, linhvuc,linhvuc_truoc):
        kehoach_muctieu_truocs = linhvuc_truoc.kehoach_muctieu_ids
        if kehoach_muctieu_truocs:
            for mt_thangtruoc in kehoach_muctieu_truocs:
                kehoach_muctieu = self.env['ekids.kehoach_muctieu'].search([
                    ("kehoach_id", "=", linhvuc.kehoach_id.id)
                    ,("muctieu_id", "=", mt_thangtruoc.muctieu_id.id)

                ],limit=1)
                if mt_thangtruoc.trangthai=="1":
                    #TH1: kế hoạch tháng trước đã đạt nếu có thì xóa đi
                    kehoach_muctieu.unlink()
                else:
                    if not kehoach_muctieu:
                        data ={
                            "sequence": mt_thangtruoc.muctieu_id.sequence,
                            "kehoach_linhvuc_id":linhvuc.id,
                            "kehoach_muctieu_thangtruoc_id": mt_thangtruoc.id,
                            "muctieu_id": mt_thangtruoc.muctieu_id.id,
                            "muctieu_them": mt_thangtruoc.muctieu_them,
                            "ghichu": mt_thangtruoc.ghichu,
                            "trangthai":"0"
                        }
                        kehoach_muctieu = self.env['ekids.kehoach_muctieu'].create(data)



    def func_kehoach_linhvuc_truocs(self,linhvuc_id,tuoi_id,kehoach_truoc):
        linhvuc_truocs = kehoach_truoc.kehoach_linhvuc_ids
        for linhvuc_truoc in linhvuc_truocs:
            if linhvuc_truoc.linhvuc_id.id == linhvuc_id and linhvuc_truoc.tuoi_id.id == tuoi_id:
                return linhvuc_truoc


