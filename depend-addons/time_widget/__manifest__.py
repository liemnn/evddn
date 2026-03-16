# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Time Widget",
    "version": "18.0",
    'price': '00',
    'currency': 'USD',
    "summary": "Time Widget For Character Field",
    "author": "FOSS INFOTECH PVT LTD",
    "website": "https://fossinfotech.com",
    "license": "Other proprietary",
    "depends": [],
    "data": [],
    'assets': {
        'web.assets_backend': [
                  "time_widget/static/src/flatpickr/flatpickr.min.css",
                  "time_widget/static/src/flatpickr/flatpickr.min.js",
                  'https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css',
                  'https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.js',
                  "time_widget/static/src/xml/time_picker.xml",
                  'time_widget/static/src/js/custom_time_picker.js',
        ]
        },
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
        'static/description/index.html',
    ],

    "installable": True,
    "auto_install": False,
    "application": False,
}
