from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class KeHoachActionAbstractModel(models.AbstractModel):
    _name = 'ekids.kehoach_action_abstractmodel'
    _description = 'Tạo kế hoạch'
    _abstract = True


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        result = super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)

        if groupby and groupby[0] == 'trangthai':
            # Lấy danh sách allowed từ context
            allowed_status = self.env.context.get('allowed_trangthai', [])

            # Toàn bộ giá trị của field selection
            selection_values = self.fields_get(allfields=['trangthai'])['trangthai']['selection']
            selection_dict = dict(selection_values)

            # Lọc chỉ các trạng thái được phép
            filtered_selection = {
                k: v for k, v in selection_dict.items()
                if not allowed_status or k in allowed_status
            }

            # Đã có sẵn trong group result
            existing_keys = [r['trangthai'] for r in result]

            # Thêm các trạng thái chưa có
            for key in filtered_selection:
                if key not in existing_keys:
                    result.append({
                        'trangthai': key,
                        'trangthai_count': 0,
                        '__count': 0,
                    })

            # Sắp xếp theo thứ tự context truyền vào, hoặc fallback mặc định
            desired_order = allowed_status or list(filtered_selection.keys())
            result.sort(key=lambda r: desired_order.index(r['trangthai']) if r['trangthai'] in desired_order else 999)

        return result


    # tao kế hoach cho học sinh
    def action_tao_kehoach_hocsinh(self):
        self.ensure_one()
        if not self.ketluan_id:
            #TH1: Chưa chọn kết luận áp dụng lập kế hoạch làm căn cứ
            raise UserError("Chưa có kết luận đánh giá, chuẩn đoán nên chưa thể lập [Kế hoạch] can thiệp"
                            + self.name
                            + ". Bạn cần lựa chọn kết quả đánh giá để làm căn cứ !")

        count =self.env['ekids.kehoach_thang'].search_count([('kehoach_id','=',self.id)])
        if count <= 0:
            if self.mau_kehoach_id and self.is_sudung_mau:
                #TH1:có mau co the copy
                self.func_tao_kehoach_theo_mau()
            else:
                #TH2: Khoong co mau
                # 1. Tạo các tháng
                self.func_tao_kehoach_thang(self.id,self.sothang,self.tu_ngay,self.den_ngay)



        return {
            'type': 'ir.actions.act_window',
            'name': 'KẾ HOẠCH CAN THIỆP [THÁNG]',
            'res_model': 'ekids.kehoach_thang',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('kehoach_id','=',self.id)],
            'context': dict(
                self.env.context,
                default_kehoach_id=self.id,
            ),
        }


    def func_tao_kehoach_theo_mau(self):
        mau =self.env['ekids.mau_kehoach'].search([('id','=',self.mau_kehoach_id.id)])
        if mau:
            mau_thangs =(self.env['ekids.mau_kehoach_thang']
                         .search([('mau_kehoach_id','=',mau.id)]))
            if mau_thangs:
                kh_thangs = self.func_tao_kehoach_thang(self.id, len(mau_thangs), self.tu_ngay, self.den_ngay)
                if kh_thangs:
                    for kh_thang in kh_thangs:
                        mau_thang = (self.env['ekids.mau_kehoach_thang']
                                      .search([('name', '=', kh_thang.name)
                                               ,('mau_kehoach_id','=',self.mau_kehoach_id.id)]))
                        if mau_thang:
                            muctieu2mau_thangs = (self.env['ekids.mau_kehoach_muctieu2thang']
                                         .search([('mau_kehoach_thang_id', '=', mau_thang.id)]))

                            if muctieu2mau_thangs:
                                for mt in muctieu2mau_thangs:
                                    data = {
                                        'kehoach_id': self.id,
                                        'kehoach_thang_id': kh_thang.id,
                                        'chuongtrinh_id': mt.chuongtrinh_id.id,
                                        'linhvuc_id': mt.linhvuc_id.id,
                                        'muctieu_id': mt.muctieu_id.id,
                                        'trangthai':'0' #doi can thiep

                                    }
                                    kh = self.env['ekids.kehoach_muctieu2thang'].create(data)





        return

    # default tao ke hoach thang

    def func_tao_kehoach_thang(self,kehoach_id,sothang,tu_ngay,den_ngay):
        if not tu_ngay or not den_ngay or int(sothang) <= 0:
            return

        tu_ngay = tu_ngay
        den_ngay = tu_ngay + timedelta(days=30)
        sothang = int(sothang) + 1
        kehoach_thangs =[]
        for i in range(1, sothang):
            data = {
                'kehoach_id': kehoach_id,
                'name': str(i),
                'tu_ngay': tu_ngay,
                'den_ngay': den_ngay,
                'trangthai':'0'

            }
            kh=self.env['ekids.kehoach_thang'].create(data)
            tu_ngay = den_ngay + timedelta(days=1)
            den_ngay = tu_ngay + timedelta(days=30)
            kehoach_thangs.append(kh)

        return kehoach_thangs





