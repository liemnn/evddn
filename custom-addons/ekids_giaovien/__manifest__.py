# -*- coding: utf-8 -*-
{
    'name': "E-kids Giáo viên",



    # any module necessary for this one to work correctly
    'depends': ['base','ekids_core','ekids_func'],

    # always loaded
    'data': [
        # 'security/ekids_security.xml',
        'security/ir.model.access.csv',



        #'wizard/wizard_copy_salary_view.xml',
        'views/ekids_coso_view.xml',
        'views/cauhinh/ekids_coso_cauhinh_view.xml',
        'views/ekids_giaovien_view.xml',
        'views/ekids_giaovien_thongtin_view.xml',
        'views/cauhinh/ekids_luong_dm_chitra_view.xml',
        'views/cauhinh/ekids_luong_dm_chamcong_view.xml',
        'views/cauhinh/ekids_giaovien_nghiphep_view.xml',


        'data/sequence.xml',
        'views/ekids_user_view.xml',


        #'views/ekids_quanly_view.xml',
        #'wizard/wizard_copy_salary_view.xml',

        'views/luong/ekids_luong_nam_view.xml',
        'views/luong/ekids_luong_thang_view.xml',
        'views/luong/phieuluong/ekids_phieuluong_action.xml',
        'views/luong/ekids_luong_view.xml',
        'views/luong/ekids_luong_sukien_view.xml',
        'views/luong/phieuluong/ekids_phieuluong_template.xml',
        'views/luong/ban_in/ekids_luong_banin_action.xml',
        'views/luong/ban_in/ekids_luong_banin_template.xml',
        'views/luong/ban_in/ekids_luong_banin_wizard_view.xml',


        'views/ekids_menu.xml',



    ],
    # only loaded in demonstration mode
    'assets': {
        'web.assets_backend': [
            'ekids_giaovien/static/src/css/ekids_style.css',
        ],
    },
}

