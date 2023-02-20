# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LeadExt(models.Model):
    _inherit = 'crm.lead'
    # _description = 'Extension for crm.lead model'

    product_ids = fields.Many2many(
        comodel_name='product.template',
        string='Products / Services', 
        default=[(6, 0, [])])
    market_id = fields.Many2one(string='Market',
        comodel_name='res.country')
    lead_company_id = fields.Many2one(string='Available Company',
        comodel_name='res.company')

    order_line_ids = fields.One2many(string="Order Lines", 
        comodel_name='test_crm.crm.order.line', 
        inverse_name='lead_id', 
        compute='_compute_order_lines')
    
    @api.depends('product_ids')
    def _compute_order_lines(self):
        for record in self:
            # def _make_test(product):
            #     ol = OrderLine()
            #     ol.test.product_id = product.id
            #     ol.lead_id = record.id
            #     return e

            # order_line_ids = list(map(lambda p : _make_test(p), record.product_ids))
            print(record.id)

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

class OrderLine(models.Model):
    _name = "test_crm.crm.order.line"
    _description = "order line for opportunity"

    product_id = fields.Many2one(
        'product.product', 
        string='Product', 
        domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, 
        ondelete='restrict', 
        check_company=True)
    product_uom_qty = fields.Float(string='Quantity', 
        digits='Product Unit of Measure', 
        required=True, 
        default=1.0)
    price_subtotal = fields.Float(compute='_compute_amount', 
        string='Subtotal', 
        store=True)
    discount = fields.Float(string="Discount", 
        default=0.0)
    
    lead_id = fields.Many2one(string='Lead Id', 
        comodel_name='crm.lead')

    # Reference field
    description = fields.Text(string='Description', 
        required=True)
    price_unit = fields.Float('Unit Price', 
        required=True, 
        default=0.0)
    tax_id = fields.Many2many('account.tax', 
        string='Taxes', 
        context={'active_test': False})
    
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            # taxes = line.tax_id.compute_all(price, 
            #     line.order_id.currency_id, 
            #     line.product_uom_qty, 
            #     product=line.product_id, 
            #     partner=line.order_id.partner_shipping_id)
            subtotal = price * product_uom_qty
            line.update({
                'price_subtotal': subtotal
            })
