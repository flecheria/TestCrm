# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CountryExt(models.Model):
    _inherit = 'res.country'

    lead_ids = fields.One2many('crm.lead', 'market_id', string='Crm Leads', copy=True)
