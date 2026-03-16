from odoo import models, fields, api, exceptions



class KeHoachMucTieu2Thang(models.Model):
    _name = "ekids.kehoach_muctieu2thang"
    _description = "[KẾ HOẠCH] THÁNG"

    sequence = fields.Integer(string="STT", default=1)
    kehoach_id = fields.Many2one("ekids.kehoach", string="Kế hoạch")
    kehoach_thang_id = fields.Many2one('ekids.kehoach_thang',string="Tháng")

    name =fields.Char(string="Chương trình/Lĩnh vực/Cấp độ", compute="_compute_muctieu_name",readonly=True)
    chuongtrinh_id = fields.Many2one('ekids.ct_chuongtrinh', string='Lựa chọn [Chương trình] can thiệp')
    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lựa chọn [Lĩnh vực] của chương trình')
    muctieu_id = fields.Many2one('ekids.ct_muctieu', string='Lựa chọn [Mục tiêu] can thiêp cho Tháng')

    hdct_mucdich = fields.Html(string="Mục đích")
    hdct_giaocu = fields.Html(string="Giáo cụ, đồ dùng")
    hdct_cach_tienhanh = fields.Html(string="Cách tiến hành")



    kythuat = fields.Html(string="Kỹ thuật/chiến lược",compute='_compute_kehoach_muctieu2thang', readonly=True,store=False)
    tieuchi = fields.Html(string="Tiêu chí",compute='_compute_kehoach_muctieu2thang', readonly=True,store=False)
    cach_danhgia = fields.Html(string="Cách [Đánh giá]",compute='_compute_kehoach_muctieu2thang', readonly=True,store=False)



    trangthai = fields.Selection([("0", "Đợi can thiệp")
                                     , ("1", "Đang can thiệp")
                                     , ("2", "Đã hoàn thành")
                                  ], string="Trạng thái [Can thiệp]"
                                 , default="0")

    is_button_ketqua = fields.Boolean(string=" Xem kết quả [Can thiệp]",
                                compute='_compute_is_button_ketqua',
                                store=False)

    ketqua_canthiep = fields.Char(string="Kết quả",compute='_compute_kehoach_muctieu2thang_ketqua_canthiep',
                                store=False)


    def _compute_kehoach_muctieu2thang_ketqua_canthiep(self):
        for r in self:
            kqs =(self.env['ekids.kehoach_ketqua2muctieu']
                  .search([('muctieu_id', '=', r.id)]))
            lamduoc =0
            khong_lamduoc=0
            luclamduoc_luckhong=0
            chua_canthiep =0
            if kqs:
                for kq in kqs:
                    if kq.ketqua == '+':
                        lamduoc += 1
                    elif kq.ketqua == '-':
                        khong_lamduoc +=1
                    elif kq.ketqua == '+/-':
                        luclamduoc_luckhong +=1
                    else:
                        chua_canthiep +=1
                r.ketqua_canthiep = '+ Làm được('+str(lamduoc)+');'
                r.ketqua_canthiep += '+/ Lúc được lúc không('+str(luclamduoc_luckhong)+');'
                r.ketqua_canthiep += '- Không làm được(' + str(khong_lamduoc) + ');'
                r.ketqua_canthiep += 'Chưa can thiệp(' + str(chua_canthiep) + ')'
            else:
                r.ketqua_canthiep=""


    def _compute_is_button_ketqua(self):
        for r in self:
            is_button_ketqua = False
            if r.trangthai =='1':
                is_button_ketqua = True
            r.is_button_ketqua = is_button_ketqua


    @api.depends('muctieu_id')
    def _compute_kehoach_muctieu2thang(self):
        for m in self:
            if m.muctieu_id:
                m.kythuat = str(m.muctieu_id.kythuat)
                m.tieuchi = str(m.muctieu_id.tieuchi)
                m.cach_danhgia = str(m.muctieu_id.cach_danhgia)
            else:
                m.kythuat=""
                m.tieuchi = ""
                m.cach_danhgia = ""




    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        result = super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)

        if groupby and groupby[0] == 'trangthai':
            # 1. Lấy danh sách tất cả các giá trị của field selection
            selection_values = self.fields_get(allfields=['trangthai'])['trangthai']['selection']

            # 2. Chuyển thành dict: {'draft': 'Nháp', ...}
            selection_dict = dict(selection_values)

            # 3. Lấy danh sách key đã có trong kết quả
            existing_keys = [r['trangthai'] for r in result]

            # 4. Thêm các key còn thiếu (chưa có record nào nhưng vẫn cần hiển thị)
            for key in selection_dict:
                if key not in existing_keys:
                    result.append({
                        'trangthai': key,
                        'trangthai_count': 0,
                        '__count': 0,
                    })

            # 5. Sắp xếp theo thứ tự mong muốn
            desired_order = ['0', '1', '2']  # <-- sửa theo field của bạn
            result.sort(key=lambda r: desired_order.index(r['trangthai']) if r['trangthai'] in desired_order else 999)

        return result
    def _compute_muctieu_name(self):
        for muctieu in self:
            ct_ma = muctieu.muctieu_id.linhvuc_id.chuongtrinh_id.ma
            ct_linhvuc = muctieu.muctieu_id.linhvuc_id.name
            capdo =muctieu.muctieu_id.dm_capdo_id.name
            muctieu.name = "["+str(ct_ma).upper()+"]" +str(ct_linhvuc) +"("+str(capdo)+")"



    def action_capnhat_ketqua_canthiep_muctieu2thang(self):
        """action view year tuition"""
        self.ensure_one()
        self.func_tao_default_ketqua_canthiep(self.id)


        return {
            'type': 'ir.actions.act_window',
            'name': self.name.upper(),
            'res_model': 'ekids.kehoach_ketqua2muctieu',
            'view_mode': 'list',
            'target': 'new',
            'domain': [('muctieu_id', '=', self.id)],
            'context': {
                'default_muctieu_id': self.id,
            }

        }




    def func_tao_default_ketqua_canthiep(self,muctieu_id):
        count = (self.env['ekids.kehoach_ketqua2muctieu']
               .search_count([('muctieu_id','=',muctieu_id)]))
        if count <=0:
            for i in range(1, 31):
                data = {
                    'muctieu_id': muctieu_id,
                    'name': str(i),
                    'ketqua': '',
                }
                self.env['ekids.kehoach_ketqua2muctieu'].create(data)

