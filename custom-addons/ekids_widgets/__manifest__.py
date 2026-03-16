{
    'name': 'E-kids Widgets',
    'description': 'Widgets dành cho hệ thống E-kids.',
    'category': 'Tools',
    'version': '1.0',
    'depends': ['base', 'web', 'mail'],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            'ekids_widgets/static/src/js/widget_attachment_preview.js',
            'ekids_widgets/static/src/xml/widget_attachment_preview.xml',
        ],
    },
    'images': [
        'static/description/home.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}