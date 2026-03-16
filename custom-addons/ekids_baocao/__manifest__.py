# -*- coding: utf-8 -*-
{
    'name': "E-kids Báo cáo",

    'description': """
Long description of module's purpose
    """,

    'author': "liemnn",
    'website': "https://www.ekids.com",


    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','ekids_func','ekids_core','ekids_giaovien','ekids_hocsinh','ekids_chitieu'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/ekids_coso_view.xml',
        'views/ekids_baocao_loinhuan_view.xml',
        'views/ekids_baocao_nguonluc_view.xml',
        'views/ekids_baocao_menu.xml',

        'views/report/ekids_baocao_action.xml',
        'views/report/ekids_baocao_loinhuan_template.xml',
        'views/report/ekids_baocao_nguonluc_template.xml',

    ],
    # only loaded in demonstration mode
    'assets': {
        'web.assets_backend': [
            'ekids_hocsinh/static/src/css/ekids_style.css',

        ],
    },
    # only loaded in demonstration mode

}

