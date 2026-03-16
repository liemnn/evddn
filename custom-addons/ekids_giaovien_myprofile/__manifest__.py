# -*- coding: utf-8 -*-
{
    'name': "E-kids ứng dụng cho Giáo viên",
     # any module necessary for this one to work correctly
    'depends': ['base','ekids_core','ekids_hocsinh','ekids_giaovien','ekids_diemdanh'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'views/ekids_giaovien_view.xml',
        'views/ekids_luong_view.xml',
        'views/ekids_giaovien_chamcong_view.xml',
        'views/ekids_menu.xml',
        'views/ekids_diemdanh_ca2ngay_wizard_inherit_view.xml',



    ],
    # only loaded in demonstration mode
    'assets': {
        'web.assets_backend': [
            'ekids_hocsinh/static/src/css/ekids_style.css',

        ],
    },
    # only loaded in demonstration mode

}

