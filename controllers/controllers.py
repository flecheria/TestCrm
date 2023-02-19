# -*- coding: utf-8 -*-
# from odoo import http


# class TestCrm(http.Controller):
#     @http.route('/test_crm/test_crm', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/test_crm/test_crm/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('test_crm.listing', {
#             'root': '/test_crm/test_crm',
#             'objects': http.request.env['test_crm.test_crm'].search([]),
#         })

#     @http.route('/test_crm/test_crm/objects/<model("test_crm.test_crm"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('test_crm.object', {
#             'object': obj
#         })
