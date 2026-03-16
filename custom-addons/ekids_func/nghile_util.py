from datetime import datetime, timedelta,date
from . import  coso_util
from odoo.osv import expression


def func_get_nghiles_trong_khoang_thoigian(self, coso, loai, tu_ngay, den_ngay):
    domain_chung =[('coso_id', '=', coso.id),
                   ('trangthai','=','1')]
    if loai:
        domain_chung.append(('loai', '=', loai))


    # Điều kiện giao nhau
    domain_ngay = [ ('tu_ngay', '<=', den_ngay),
                    ('den_ngay', '>=', tu_ngay) ]

    domain = expression.AND([
        domain_chung,
        domain_ngay

    ])


    nghiles = self.env['ekids.nghile'].search(domain)

    result = {}
    if nghiles:
        for nghile in nghiles:
            # nghi le thong thuong
            ngay_batdau = nghile.tu_ngay
            if ngay_batdau < tu_ngay:
                ngay_batdau = tu_ngay

            ngay_ketthuc = nghile.den_ngay
            if ngay_ketthuc > den_ngay:
                ngay_ketthuc = den_ngay
            ngay = ngay_batdau
            while ngay <= ngay_ketthuc:
                if coso_util.func_is_coso_hoatdong(coso, ngay):
                    result[str(ngay)] = nghile
                ngay += timedelta(days=1)

    return result