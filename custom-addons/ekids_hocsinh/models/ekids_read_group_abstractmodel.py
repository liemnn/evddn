from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class ReadGroupAbstractModel(models.AbstractModel):
    _name = 'ekids.read_group'
    _description = 'Tạo lập trang thai group'
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
