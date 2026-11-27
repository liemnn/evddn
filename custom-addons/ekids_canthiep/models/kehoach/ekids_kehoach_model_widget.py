# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class KeHoachWidgetLinhVucApi(models.Model):
    _inherit = 'ekids.kehoach'

    def get_danhmuc_them_linhvuc(self):
        """Lấy toàn bộ danh mục Chương trình, Lĩnh vực và Độ tuổi trực tiếp từ danh mục gốc"""
        KeHoachLinhVuc = self.env['ekids.kehoach_linhvuc']

        CtModel = self.env[KeHoachLinhVuc._fields['chuongtrinh_id'].comodel_name]
        LvModel = self.env[KeHoachLinhVuc._fields['linhvuc_id'].comodel_name]
        TuoiModel = self.env[KeHoachLinhVuc._fields['tuoi_id'].comodel_name]

        # 1. Lấy toàn bộ Chương trình (dùng sudo() để tránh bị record rule ẩn mất danh mục dùng chung)
        ct_order = 'sequence, id' if 'sequence' in CtModel._fields else 'id'
        chuongtrinhs = CtModel.sudo().search_read([], ['id', 'name'], order=ct_order)

        # 2. Lấy toàn bộ Lĩnh vực kèm chuongtrinh_id
        lv_order = 'sequence, id' if 'sequence' in LvModel._fields else 'id'
        lv_rows = LvModel.sudo().search_read([], ['id', 'name', 'chuongtrinh_id'], order=lv_order)
        linhvucs = [
            {
                'id': r['id'],
                'name': r['name'],
                'ct_id': r['chuongtrinh_id'][0] if r.get('chuongtrinh_id') else 0,
            }
            for r in lv_rows
        ]

        # 3. Lấy toàn bộ Độ tuổi kèm chuongtrinh_id
        tuoi_order = 'sequence, id' if 'sequence' in TuoiModel._fields else 'id'
        tuoi_rows = TuoiModel.sudo().search_read([], ['id', 'name', 'chuongtrinh_id'], order=tuoi_order)
        tuois = [
            {
                'id': r['id'],
                'name': r['name'],
                'ct_id': r['chuongtrinh_id'][0] if r.get('chuongtrinh_id') else 0,
                'lv_id': 0,
            }
            for r in tuoi_rows
        ]

        return {
            'chuongtrinhs': chuongtrinhs,
            'linhvucs': linhvucs,
            'tuois': tuois,
        }

    def action_widget_them_linhvuc(self, chuongtrinh_id, linhvuc_id, tuoi_id):
        """Thêm lĩnh vực từ widget & tự động đồng bộ vào Kết luận (khi is_canthiep_ketluan == False)"""
        self.ensure_one()
        if self.is_canthiep_ketluan:
            raise UserError("Kế hoạch này đang can thiệp theo khung Kết luận, không thể tự thêm lĩnh vực.")
        if self.trangthai != '0':
            raise UserError("Chỉ được phép thêm lĩnh vực khi kế hoạch đang ở trạng thái 'Đang lập'.")
        if not (chuongtrinh_id and linhvuc_id and tuoi_id):
            raise UserError("Vui lòng chọn đầy đủ Chương trình, Lĩnh vực và Độ tuổi.")

        chuongtrinh_id = int(chuongtrinh_id)
        linhvuc_id = int(linhvuc_id)
        tuoi_id = int(tuoi_id)

        KeHoachLinhVuc = self.env['ekids.kehoach_linhvuc'].sudo()
        existing = KeHoachLinhVuc.search([
            ('kehoach_id', '=', self.id),
            ('chuongtrinh_id', '=', chuongtrinh_id),
            ('linhvuc_id', '=', linhvuc_id),
            ('tuoi_id', '=', tuoi_id),
        ], limit=1)
        if existing:
            return {'status': 'exists', 'id': existing.id}

        lv_master = self.env['ekids.ct_linhvuc'].browse(linhvuc_id)
        seq = lv_master.sequence or (max(self.kehoach_linhvuc_ids.mapped('sequence') or [0]) + 10)

        new_lv = KeHoachLinhVuc.create({
            'kehoach_id': self.id,
            'chuongtrinh_id': chuongtrinh_id,
            'linhvuc_id': linhvuc_id,
            'tuoi_id': tuoi_id,
            'sequence': seq,
        })

        # Đồng bộ ngược vào Kết luận (ketluan_id) để kế thừa tháng sau
        ketluan = self.ketluan_id
        if ketluan:
            linhvuc_ids = ketluan.linhvuc_ids
            ModelKL2LV = self.env[linhvuc_ids._name].sudo()

            linhvuc_tontai = linhvuc_ids.filtered(
                lambda r: r.linhvuc_id.id == linhvuc_id
                          and r.tuoi_id.id == tuoi_id
                          and (not r.chuongtrinh_id or r.chuongtrinh_id.id == chuongtrinh_id)
            )
            if not linhvuc_tontai:
                data = {
                    'ketluan_id': ketluan.id,
                    'chuongtrinh_id': chuongtrinh_id,
                    'linhvuc_id': linhvuc_id,
                    'tuoi_id': tuoi_id,
                }
                if 'sequence' in ModelKL2LV._fields:
                    data['sequence'] = seq

                ModelKL2LV.create(data)

        return {'status': 'created', 'id': new_lv.id}

    def action_widget_doi_vitri_linhvuc(self, lv_id, direction):
        """Hoán đổi vị trí (sequence) lên/xuống giữa 2 lĩnh vực liền kề và đồng bộ Kết luận"""
        self.ensure_one()
        if self.is_canthiep_ketluan or self.trangthai != '0':
            raise UserError("Không được thay đổi vị trí lĩnh vực ở trạng thái hiện tại.")

        lines = self.kehoach_linhvuc_ids.sorted(key=lambda r: (r.sequence, r.id))
        for idx, line in enumerate(lines, start=1):
            line.sequence = idx * 10

        line_ids = lines.ids
        if lv_id not in line_ids:
            return False

        pos = line_ids.index(lv_id)
        swap_pos = pos - 1 if direction == 'up' else pos + 1
        if swap_pos < 0 or swap_pos >= len(lines):
            return False

        curr_line = lines[pos]
        target_line = lines[swap_pos]
        curr_line.sequence, target_line.sequence = target_line.sequence, curr_line.sequence

        # Đồng bộ sequence về Kết luận
        if self.ketluan_id and hasattr(self.ketluan_id, 'ketluan_linhvuc_ids'):
            for l in [curr_line, target_line]:
                kl_match = self.ketluan_id.ketluan_linhvuc_ids.filtered(
                    lambda r: r.linhvuc_id.id == l.linhvuc_id.id and r.tuoi_id.id == l.tuoi_id.id
                )
                if kl_match:
                    kl_match.write({'sequence': l.sequence})

        return True

    def action_widget_xoa_linhvuc(self, lv_id):
        """Xóa lĩnh vực trống (0 mục tiêu) khỏi Kế hoạch tháng và đồng thời xóa khỏi Kế hoạch khung (Kết luận)"""
        self.ensure_one()
        if self.is_canthiep_ketluan:
            raise UserError("Kế hoạch theo khung Kết luận không cho phép xóa lĩnh vực.")
        if self.trangthai != '0':
            raise UserError("Chỉ được phép xóa lĩnh vực khi kế hoạch đang ở trạng thái 'Đang lập'.")

        lv = self.env['ekids.kehoach_linhvuc'].browse(int(lv_id))
        if not lv.exists():
            return True

        # 1. Chỉ cho xóa khi lĩnh vực trong kế hoạch không còn mục tiêu nào
        if lv.kehoach_muctieu_ids:
            raise UserError(
                f"Lĩnh vực [{lv.linhvuc_id.name}] đang có {len(lv.kehoach_muctieu_ids)} mục tiêu. "
                "Vui lòng xóa hết mục tiêu bên trong trước khi xóa lĩnh vực!"
            )

        # Lưu lại thông tin nhận diện trước khi unlink lv
        linhvuc_id = lv.linhvuc_id.id
        tuoi_id = lv.tuoi_id.id
        chuongtrinh_id = lv.chuongtrinh_id.id if 'chuongtrinh_id' in lv._fields and lv.chuongtrinh_id else False

        # 2. Tìm Kế hoạch khung / Kết luận liên kết (hoặc kế hoạch 6 tháng gần nhất của học sinh)
        ketluan = self.ketluan_id

        # 3. Xóa dòng lĩnh vực tương ứng bên trong Kế hoạch khung (ketluan.linhvuc_ids)
        if ketluan and hasattr(ketluan, 'linhvuc_ids'):


            kl_linhvuc_tontai = ketluan.linhvuc_ids.sudo().filtered(
                lambda r: r.linhvuc_id.id == linhvuc_id
                          and r.tuoi_id.id == tuoi_id
                          and r.chuongtrinh_id.id == chuongtrinh_id

            )
            if kl_linhvuc_tontai:
                kl_linhvuc_tontai.unlink()

        # 4. Xóa dòng lĩnh vực ở Kế hoạch tháng hiện tại
        lv.unlink()
        return True