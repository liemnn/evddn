# -*- coding: utf-8 -*-
{
    'name': "E-kids Phụ huynh",
     # any module necessary for this one to work correctly
    'depends': ['base','ekids_core','ekids_hocsinh','ekids_func'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/ekids_app_template_view.xml',
        'views/ekids_lichhoc_template_view.xml',


        'views/ekids_hocphi_view.xml',
        'views/ekids_thongbao_view.xml',
        'views/ekids_phuhuynh_menu.xml',



    ],
    # only loaded in demonstration mode
    'assets': {
        'web.assets_backend': [
            'ekids_hocsinh/static/src/css/ekids_style.css',

        ],
    },
    # only loaded in demonstration mode

}

