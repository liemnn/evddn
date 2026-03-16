# -*- coding: utf-8 -*-
{
    'name': "E-kids Điểm danh",
    'description': 'Module quản lý điểm danh học sinh và giáo viên.',

    'author': "My Company",
    'website': "https://www.ekids.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'ekids_func','ekids_core','ekids_hocsinh','ekids_giaovien'],

    # always loaded
    'data': [
        # 'security/ekids_security.xml',
        'security/ir.model.access.csv',
        'views/ekids_coso_view.xml',
        'views/giaovien/ekids_coso_giaovien_view.xml',

        'views/hocsinh/ekids_diemdanh_view.xml',
        'views/hocsinh/ekids_diemdanh_hocsinh2thang_view.xml',
        'views/hocsinh/ekids_diemdanh_hocsinh2ngay_view.xml',
        'views/hocsinh/ekids_diemdanh_ca2ngay_view.xml',
        'views/hocsinh/ekids_hocsinh_nghiphep_view.xml',
        'views/hocsinh/ekids_hocsinh_nghiphep_inherit_view.xml',
        'views/hocsinh/ekids_hocsinh_nghiphep_wizard_view.xml',



        'views/giaovien/ekids_chamcong_loai_view.xml',
        'views/giaovien/ekids_chamcong_loai2thang_view.xml',
        'views/giaovien/ekids_chamcong_kpi2thang_view.xml',
        'views/giaovien/ekids_chamcong_kpi2thang_ketqua_view.xml',
        'views/giaovien/ekids_chamcong_giaovien2thang_view.xml',
        'views/giaovien/ekids_chamcong_giaovien2ngay_view.xml',
        'views/giaovien/ekids_giaovien_nghiphep_wizard_view.xml',
        'views/giaovien/ekids_chamcong_congviec2thang_view.xml',
        'views/giaovien/ekids_chamcong_congviec2thang_giatri_view.xml',
        'views/giaovien/ekids_chamcong_congviec2ngay_giatri_wizard_view.xml',
        'views/giaovien/ekids_giaovien_nghiphep_view.xml',
        'views/giaovien/ekids_giaovien_nghiphep_inherit_view.xml',


        'views/ekids_nghile_inherit_view.xml',
        'views/ekids_diemdanh_ca2ngay_wizard_view.xml',


        'views/ekids_menu.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ekids_diemdanh/static/src/css/ekids_style.css',
            'ekids_diemdanh/static/src/css/ekids_diemdanh.css',
            'ekids_diemdanh/static/src/js/widget_hocsinh_diemdanh.js',
            'ekids_diemdanh/static/src/js/diemdanh_controller.js',
            'ekids_diemdanh/static/src/xml/widget_hocsinh_diemdanh.xml',
            'ekids_diemdanh/static/src/js/widget_giaovien_chamcong.js',
            'ekids_diemdanh/static/src/js/chamcong_controller.js',
            'ekids_diemdanh/static/src/xml/widget_giaovien_chamcong.xml',
            'ekids_diemdanh/static/src/js/widget_giaovien_congviec.js',
            'ekids_diemdanh/static/src/js/congviec_controller.js',
            'ekids_diemdanh/static/src/xml/widget_giaovien_congviec.xml',
        ],
    },
    'fonts': [

    ],
}
