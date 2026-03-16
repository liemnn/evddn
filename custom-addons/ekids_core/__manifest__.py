# -*- coding: utf-8 -*-
{
    'name': "E-kids Core Flatform",

    'description': """
Long description of module's purpose
    """,

    'author': "liemnn",
    'website': "https://www.ekids.com",


    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','web'],

    # always loaded
    'data': [
        'security/ekids_security.xml',
        'security/ir.model.access.csv',

        'views/ekids_dm_tinh_view.xml',
        'views/ekids_dm_xa_view.xml',
        'views/ekids_coso_view.xml',
        'views/ekids_coso_cauhinh_view.xml',

        'views/nghile/ekids_nghile_nam_view.xml',
        'views/nghile/ekids_nghile_view.xml',

        'views/thongbao/ekids_thongbao_phuhuynh_view.xml',




        'views/ekids_core_menu.xml',
        #'views/ekids_loaichi_view.xml',



    ],
    # only loaded in demonstration mode
    'assets': {
        'web.assets_backend': [
            'ekids_core/static/src/css/ekids_style.css',

        ],
    },
}


