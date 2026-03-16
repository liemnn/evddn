{
    'name': 'Password Visibility Toggle',
    'author': 'Odoo Hub',
    'category': 'Tools',
    'summary': 'This Odoo module adds a password visibility toggle button to the login page, allowing users to easily show or hide password. show password password visible hidden password visible password password show login form show hide password password toggle toggle password visibility login page enhancement eye icon password toggle view password unmask password password input toggle password reveal secure login field toggle password visibility button show password button odoo login improvement password visibility switch user friendly login accurate login input toggle login accessibility secure password input login UX login UI enhancement password visibility control odoo login UI password field enhancement show password on login password input visibility toggle login screen password toggle odoo authentication UI password form improvement show hide password in login screen view password login page show password login page hide password login page web responsive login odoo web login page web backend login odoo login web odoo login page odoo page login web responsive signin odoo web signin page web backend signin odoo signup page odoo signin page signup odoo signup form login odoo signin screen toggle password signup page odoo authentication screen customize login page show hide password in sign in screen view password signin page show password signup page hide password signin page',
    'description': """
        The Password Visibility Toggle module enhances the login page by adding a simple and intuitive toggle button to show or hide the password input. This feature improves the user experience, allowing users to verify their password before submission, ensuring better accuracy during login.
        By clicking the eye icon next to the password field, users can easily toggle between viewing the password in plain text or hiding it for privacy. This not only helps reduce login errors but also increases security by giving users more control over their login credentials.
        Ideal for improving accessibility and user-friendliness in login forms, this module is especially beneficial for users on devices with small screens or for those who struggle with remembering passwords. It ensures a smooth and secure login process, improving both user satisfaction and overall security.
        Features:
        - Password visibility toggle button on the login form
        - Show/Hide password functionality
        - User-friendly, easy to use for better login accuracy
        - Secure and privacy-conscious
    """,
    'maintainer': 'Odoo Hub',
    'website': 'https://apps.odoo.com/apps/modules/browse?author=Odoo%20Hub',
    'version': '1.0',
    'depends': ['base', 'web'],
    'data': [
        'view/web_login_template.xml',
    ],
    'images': ['static/description/banner.png'],
    'live_test_url': 'https://youtu.be/hEiXBWF5vuY',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
