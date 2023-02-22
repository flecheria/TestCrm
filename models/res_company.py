# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CompanyExt(models.Model):
    _inherit = 'res.company'
    # _description = 'Extension for res.company model'

    lead_ids = fields.One2many('crm.lead', 'lead_company_id', string='Crm Leads', copy=True)
