# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LeadExt(models.Model):
    _inherit = 'crm.lead'
    # _description = 'Extension for crm.lead model'

    product_ids = fields.Many2many(
        comodel_name='product.template',
        string='Products / Services')
    market_id = fields.Many2one(string='Market',
        comodel_name='res.country')
    lead_company_id = fields.Many2one(string='Company',
        comodel_name='res.company')

class CountryExt(models.Model):
    _inherit = 'res.country'
    # _description = 'Extension for res.country model'

    lead_ids = fields.One2many(string='Crm Leads', 
        comodel_name='crm.lead', 
        inverse_name='market_id', 
        copy=True)

class CompanyExt(models.Model):
    _inherit = 'res.company'
    # _description = 'Extension for res.company model'

    lead_ids = fields.One2many(string='Crm Leads', 
        comodel_name='crm.lead', 
        inverse_name='lead_company_id', 
        copy=True)
