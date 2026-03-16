{
    "name": "ekids_list_icon",
    "version": "1.0",
    "summary": "Demo: list icon column widget for Odoo 18",
    "author": "ChatGPT",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        "views/model_a_views.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "ekids_list_icon/static/src/js/icon_state_widget.js",
            "ekids_list_icon/static/src/xml/icon_state_widget.xml"
        ]
    },
    "installable": True,
    "application": False
}
