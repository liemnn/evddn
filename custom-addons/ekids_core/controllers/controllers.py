# -*- coding: utf-8 -*-
# from odoo import http


# class Ekids-core(http.Controller):
#     @http.route('/ekids-core/ekids-core', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ekids-core/ekids-core/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ekids-core.listing', {
#             'root': '/ekids-core/ekids-core',
#             'objects': http.request.env['ekids-core.ekids-core'].search([]),
#         })

#     @http.route('/ekids-core/ekids-core/objects/<model("ekids-core.ekids-core"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ekids-core.object', {
#             'object': obj
#         })

