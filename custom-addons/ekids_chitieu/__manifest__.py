# -*- coding: utf-8 -*-
{
    'name': "E-kids Thu chi",

    'author': "My Company",
    'website': "https://www.ekids.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'ekids_core'],

    # always loaded
    'data': [
        # 'security/ekids_security.xml',
        'security/ir.model.access.csv',
        'wizard/chitieu_report.xml',
        'wizard/chitieu_thang.xml',
        'views/ekids_coso_view.xml',
        'views/ekids_dm_loaichi_view.xml',
        'views/ekids_chitieu_view.xml',
        'views/ekids_chitieu_thang_view.xml',
        'views/ekids_chitieu_nam_view.xml',
        'views/ekids_menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ekids_chitieu/static/src/css/style.css',
            'ekids_chitieu/static/src/css/custom_report_style.css',

        ],
    },
    'fonts': [

    ],
}
