from datetime import datetime, timedelta,date


def func_get_kehoach_hocsinh(self, hocsinh):
    kehoach = self.env['ekids.kehoach'].search([
        ('hocsinh_id', '=', hocsinh.id),
    ]
        , order="tu_ngay desc, id desc", limit=1)
    return kehoach





