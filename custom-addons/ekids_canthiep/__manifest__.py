# -*- coding: utf-8 -*-
{
    'name': "E-kids Chương trình [Can thiệp]",

    'description': """
Long description of module's purpose
    """,

    'author': "liemnn",
    'website': "https://www.ekids.com",


    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'ekids_core','ekids_func','ekids_hocsinh','ekids_giaovien'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/ekids_coso_view.xml',



        'views/chuongtrinh/ekids_ct_chuongtrinh_view.xml',
        'views/chuongtrinh/ekids_ct_tuoi_view.xml',
        'views/chuongtrinh/ekids_ct_linhvuc_view.xml',
        'views/chuongtrinh/ekids_ct_muctieu_view.xml',
        'views/chuongtrinh/ekids_ct_dm_roiloan_view.xml',



        'views/mau_kehoach/ekids_mau_kehoach_view.xml',
        'views/mau_kehoach/ekids_mau_kehoach_roiloan_dikem_view.xml',
        'views/mau_kehoach/ekids_mau_kehoach_thang_view.xml',
        'views/mau_kehoach/ekids_mau_kehoach_muctieu2thang_view.xml',

        'views/kehoach/ekids_hocsinh_inherit_view.xml',
        'views/kehoach/ekids_kehoach_ketluan_view.xml',
        'views/kehoach/ekids_kehoach_view.xml',
        'views/kehoach/ekids_kehoach_linhvuc_view.xml',
        'views/kehoach/ekids_kehoach_muctieu_view.xml',

        'views/ekids_menu.xml',


    ],
    # only loaded in demonstration mode
    'assets': {
        'web.assets_backend': [
            'ekids_canthiep/static/src/css/ekids_style.css',
            'ekids_canthiep/static/src/css/ekids_canthiep.css',
            
        ],
    },





}