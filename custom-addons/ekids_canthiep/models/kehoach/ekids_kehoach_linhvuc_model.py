from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression


class KeHoach2LinhVuc(models.Model):
    _name = 'ekids.kehoach_linhvuc'
    _description = 'Các mục tiêu cho kế hoạch'
    _order = "sequence asc"

    sequence = fields.Integer(string="STT", default=1)
    kehoach_id = fields.Many2one("ekids.kehoach", string="Thuộc kế hoạch nào",
                                 required=True,
                                 ondelete="cascade")

    chuongtrinh_id = fields.Many2one(
        'ekids.ct_chuongtrinh',
        string='Chương trình',
        required=True,
        ondelete="cascade",
    )

    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực', required=True, ondelete="cascade")
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi', required=True, ondelete="cascade")

    kehoach_muctieu_ids = fields.One2many(
        comodel_name="ekids.kehoach_muctieu",
        inverse_name="kehoach_linhvuc_id",
        string="Các mục tiêu cho kế hoạch"
    )

    is_readonly = fields.Boolean(compute="_compute_is_readonly")

    tong_muctieu_dat= fields.Integer(compute="_compute_tong_muctieu_dat")


    def func_capnhat_kehoach_muctieu_truoc(self):
        kehoach_muctieus = self.kehoach_muctieu_ids
        if kehoach_muctieus:
            kehoach_muctieus.write({'kehoach_muctieu_truoc_id': False})

            # Ép Odoo đồng bộ dữ liệu xuống PostgreSQL ngay lập tức, triệt tiêu lỗi vòng lặp cache
            self.env.flush_all()

            # 🌟 BƯỚC 2: Tính toán chuỗi tịnh tiến
            muctieu_truoc = None
            for kehoach_muctieu in kehoach_muctieus:
                if muctieu_truoc:
                    # Dùng write() trực tiếp hoặc gán thuộc tính đều được
                    kehoach_muctieu.write({'kehoach_muctieu_truoc_id': muctieu_truoc.id})
                else:
                    kehoach_muctieu.write({'kehoach_muctieu_truoc_id': False})

                # 🌟 CHÚ Ý: Dòng này bắt buộc phải thụt lề nằm TRONG vòng lặp for
                muctieu_truoc = kehoach_muctieu

    @api.depends("kehoach_muctieu_ids","kehoach_muctieu_ids.trangthai")
    def _compute_tong_muctieu_dat(self):
        for record in self:
            tong=0
            kehoach_muctieus = record.kehoach_muctieu_ids
            if kehoach_muctieus:
                for kehoach_muctieu in kehoach_muctieus:
                    if kehoach_muctieu.trangthai=="1":
                        tong +=1
            record.tong_muctieu_dat=tong

    def _compute_is_readonly(self):
        for record in self:
            record.is_readonly = record.kehoach_id.is_readonly


    def action_xem_danhsach_ct_muctieu(self):
        self.ensure_one()

        wizard_id = self.env.context.get('default_wizard_id')
        # Tìm ID của Form View của bảng tạm Wizard anh em mình vừa tạo ở Bước 2
        wizard_form_id = self.env.ref('ekids_canthiep.kehoach_linhvuc_wizard_form').id
        muctieu_thangtruoc_ids=[]
        kehoach_muctieus = self.kehoach_muctieu_ids
        if kehoach_muctieus:
            for kehoach_muctieu in kehoach_muctieus:
                if kehoach_muctieu.kehoach_muctieu_thangtruoc_id:
                    muctieu_thangtruoc_ids.append(kehoach_muctieu.muctieu_id.id)

        url= {
            'type': 'ir.actions.act_window',
            'name': 'CÁC MỤC TRONG LĨNH VỰC CỦA KẾ HOẠCH',
            'res_model': 'ekids.kehoach_linhvuc_wizard',
            'view_mode': 'form',
            'views': [(wizard_form_id, 'form')],
            'target': 'new',
            'context': {
                'search_default_linhvuc_id': self.linhvuc_id.id,
                'search_default_tuoi_id': self.tuoi_id.id,

                # 🌟 BỔ SUNG DÒNG NÀY: Truyền ID dòng hiện tại sang để điền vào trường bắt buộc của Wizard
                'default_kehoach_linhvuc_id': self.id,

                'default_kehoach_id': self.kehoach_id.id,
                'default_linhvuc_id': self.linhvuc_id.id,
                'default_tuoi_id': self.tuoi_id.id,
                'default_hocsinh_id': self.kehoach_id.hocsinh_id.id,
                'default_muctieu_thangtruoc_ids':muctieu_thangtruoc_ids,

                'edit': False,
                'create': True,
                'delete': False,
            },
        }
        if wizard_id:
            url["res_id"]= wizard_id
        return url


    def action_them_muctieu_vao_kehoach_linhvuc(self):
        self.ensure_one()
        ct_muctieu_ids =[]
        kehoach_muctieus = self.kehoach_muctieu_ids
        if kehoach_muctieus:
            for kehoach_muctieu in kehoach_muctieus:
                ct_muctieu_ids.append(kehoach_muctieu.muctieu_id.id)
        domain =[("linhvuc_id","=",self.linhvuc_id.id),("tuoi_id","=",self.tuoi_id.id)]
        if len(ct_muctieu_ids)>0:
            domain_muctieu = [("id", "not in", ct_muctieu_ids)]
            domain = expression.AND([domain, domain_muctieu])


        list_view_id = self.env.ref('ekids_canthiep.ct_muctieu_lap_kehoach_list').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'LỰA CHỌN MỤC TIÊU VÀO KẾ HOẠCH',
            'res_model': 'ekids.ct_muctieu',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'new',
            'domain':domain,
            'context': {
                'default_kehoach_linhvuc_id': self.id,
                'create': False,
                'edit': False,
                'delete': False,

            },
            # 🌟 GIẢI PHÁP CHÍ MẠNG: Khai báo flag ép Web Client tắt chế độ Selection Mode
            'flags': {
                'select': False,  # Tắt ô checkbox đầu dòng trên màn hình lớn
                'list': {
                    'select': False,  # Khóa triệt để cấu trúc render list
                    'selectable': False,  # Chuyển từ trạng thái "Chọn dữ liệu" sang "Xem dữ liệu"
                },
                'multi_select': False  # Vô hiệu hóa tính năng gom nhóm checkbox trên Mobile
            }

        }

    def action_gv_tu_taomoi_muctieu(self):
        self.ensure_one()
        form_view_id = self.env.ref('ekids_canthiep.kehoach_muctieu_gv_tu_taomoi_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'TẠO [MỤC TIÊU] CHO KẾ HOẠCH',
            'res_model': 'ekids.kehoach_muctieu',
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'target': 'new',
            'context': {
                'default_kehoach_id': self.kehoach_id.id,
                'default_kehoach_linhvuc_id': self.id,
                'default_linhvuc_id': self.linhvuc_id.id,
                'default_tuoi_id': self.tuoi_id.id
            }

        }


    def func_tao_kehoach_muctieu(self,muctieu):
        count = self.env['ekids.kehoach_muctieu'].search_count([
            ('kehoach_linhvuc_id', '=', self.id)
            , ('muctieu_id', '=',  muctieu.id)
        ])
        if count <= 0:
            data = {
                'kehoach_linhvuc_id': self.id,
                'muctieu_id': muctieu.id,
                'sequence': muctieu.sequence,
                'trangthai': '0',
            }
            muctieu_thangtruoc = self.func_get_muctieu_thangtruoc(muctieu)
            if muctieu_thangtruoc:
                data["kehoach_muctieu_thangtruoc_id"] = muctieu_thangtruoc.id

            muctieu_new = self.env['ekids.kehoach_muctieu'].create(data)
            return muctieu_new






    def func_get_muctieu_thangtruoc(self,muctieu):
        kehoach = self.kehoach_id
        if kehoach:
            kehoach_thangtruoc = kehoach.kehoach_truoc_id
            if kehoach_thangtruoc:

                kehoach_linhvucs=kehoach_thangtruoc.kehoach_linhvuc_ids
                if kehoach_linhvucs:
                    for kehoach_linhvuc in kehoach_linhvucs:
                        kehoach_muctieus = kehoach_linhvuc.kehoach_muctieu_ids
                        if kehoach_muctieus:
                            for kehoach_muctieu in kehoach_muctieus:
                                if kehoach_muctieu.muctieu_id.id == muctieu.id:
                                    return kehoach_muctieu

