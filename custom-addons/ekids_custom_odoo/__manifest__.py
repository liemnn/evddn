{
    "name": "Ekids Hiệu chỉnh Odoo18",
    "version": "18.0",
    "summary": "Hiệu chỉnh Odoo18",
    "category": "Web",
    "author": "Ekids",
    "depends": ["base","web"],
    'data': [
        'views/odoo_login_view.xml',
        'views/assets.xml',

      ],
    "assets": {

        "web.assets_backend": [
            'ekids_custom_odoo/static/src/js/user_menu.js',
            "ekids_custom_odoo/static/src/js/custom_title.js",
        ],
        "web.assets_frontend": [
            "ekids_custom_odoo/static/src/manifest.json",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
