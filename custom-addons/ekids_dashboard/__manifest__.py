# -*- coding: utf-8 -*-
{
    'name': 'eKids - Dashboard - Khung nhìn trực quan',
    'version': '18.0.1.0.0',
    'category': 'Education',
    'summary': 'Dashboard giám sát hoạt động can thiệp real-time trên Odoo 18',
    'depends': ['base', 'web', 'ekids_core','ekids_func','ekids_canthiep','ekids_hocsinh','ekids_giaovien'],
    'data': [
        'security/ir.model.access.csv',
        'views/ekids_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ekids_dashboard/static/src/css/canthiep_dashboard.scss',
            'ekids_dashboard/static/src/js/canthiep_dashboard.js',
            'ekids_dashboard/static/src/xml/canthiep_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}