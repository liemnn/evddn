# -*- coding: utf-8 -*-
{
    'name': "E-kids Phụ huynh",
     # any module necessary for this one to work correctly
    'depends': ['base','ekids_core','ekids_hocsinh','ekids_func','ekids_diemdanh'],
    "icons": [
        {
          "src": "/ekids_phuhuynh/static/src/img/icon_192.png",
          "sizes": "192x192",
          "type": "image/png"
        },
        {
          "src": "/ekids_phuhuynh/static/src/img/icon_512.png",
          "sizes": "512x512",
          "type": "image/png"
        }
      ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/ekids_home_template_view.xml',
        'views/ekids_lichhoc_template_view.xml',
        'views/ekids_hocphi_template_view.xml',
        'views/ekids_chat_template_view.xml',
        'views/ekids_hocphi_thanhtoan_template_view.xml',
        'views/ekids_nghiphep_template_view.xml',
        'views/ekids_info_template_view.xml',


    ],
    # only loaded in demonstration mode
    'assets': {
        'web.assets_backend': [
            'ekids_hocsinh/static/src/css/ekids_style.css',

        ],
    },
    # only loaded in demonstration mode

}

