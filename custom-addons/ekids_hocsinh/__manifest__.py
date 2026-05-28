# -*- coding: utf-8 -*-
{
    'name': "E-kids Học sinh",



    # any module necessary for this one to work correctly
    'depends': ['base','ekids_func','ekids_core','ekids_giaovien'],

    # always loaded
    'data': [
        # 'security/ekids_security.xml',
        'security/ir.model.access.csv',

        #'wizard/wizard_copy_salary_view.xml',
        'views/ekids_coso_view.xml',
        'views/ekids_hocsinh_view.xml',
        'views/ekids_hocsinh_phuhuynh_view.xml',
        'views/ekids_hocsinh_view.xml',
        'views/ekids_hocsinh_lichsu_canthiep_view.xml',
        'views/ekids_user_view.xml',


        'views/cauhinh/ekids_hocphi_dm_thu_bantru_view.xml',
        'views/cauhinh/ekids_hocphi_dm_ca_view.xml',
        'views/cauhinh/ekids_hocphi_dm_chinhsach_giam_view.xml',
        'views/cauhinh/ekids_hocsinh_ca_canthiep_view.xml',
        'views/cauhinh/ekids_hocsinh_nghiphep_view.xml',

        #'views/ekids_quanly_view.xml',
        #'wizard/wizard_copy_salary_view.xml',

        'views/hocphi/phieuthu/ekids_hocphi_in_template.xml',
        'views/hocphi/phieuthu/ekids_hocphi_in_action.xml',

        'views/hocphi/ekids_hocphi_nam_view.xml',
        'views/hocphi/ekids_hocphi_thang_view.xml',
        'views/hocphi/ekids_hocphi_view.xml',
        'views/hocphi/ekids_hocphi_bantru_view.xml',
        'views/hocphi/ekids_hocphi_ca_view.xml',
        'views/hocphi/ekids_hocphi_duoctru_view.xml',
        'views/hocphi/ekids_hocphi_thungoai_view.xml',
        'views/hocphi/ban_in/ekids_hocphi_banin_action.xml',
        'views/hocphi/ban_in/ekids_hocphi_banin_template.xml',
        'views/hocphi/ban_in/ekids_hocphi_banin_wizard_view.xml',


        'views/taichinh/ekids_lichsu_giaodich_view.xml',





        'views/ekids_menu.xml',
        'data/sequence.xml',




    ],
    # only loaded in demonstration mode
    'assets': {
        'web.assets_backend': [
            'ekids_hocsinh/static/src/css/ekids_style.css',
            'ekids_hocsinh/static/src/css/ekids_odoo_custom.css',
        ],
    },


}

