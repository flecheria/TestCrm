# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import get_lang
from odoo.tools import float_is_zero, float_compare, float_round
from collections import defaultdict


class CrmLead(models.Model):
    _inherit = 'crm.lead'
    # _description = 'Extension for crm.lead model'

    product_ids = fields.Many2many(
        'product.product',
        string='Products / Services',
        default=[(6, 0, [])])
    market_id = fields.Many2one('res.country', default=lambda self: self.env.company.country_id, string='Market')
    lead_company_id = fields.Many2one('res.company', default=lambda self: self.env.company, string='Available Company')
    crm_order_line = fields.One2many('crm.order.line', 'lead_id', string="Order Lines")

    @api.model_create_multi
    def create(self, vals_list):
        result = super(CrmLead, self).create(vals_list)
        for rec in result:
            if rec.product_ids:
                rec._onchange_product_ids()
        return result
    
    @api.onchange('product_ids')
    def _onchange_product_ids(self):
        for record in self:
            order_lines_data = [fields.Command.clear()]
            for product in record.product_ids:
                vals = {
                    'product_id': product._origin.id,
                    'name': product._origin.display_name,
                    'product_uom_qty': 1,
                }
                order_lines_data += [
                    fields.Command.create(vals)
                ]
            record.crm_order_line = order_lines_data
        
    def write(self, vals):
        res = super(CrmLead, self).write(vals)
        if 'stage_id' in vals:
            if self.stage_id.is_won:
                order_line_vals = []
                for line in self.crm_order_line:
                    order_line_vals.append(fields.Command.create(line._prepare_order_line()))
                sale_order = self.env['sale.order'].create({
                    'partner_id': self.partner_id.id,
                    'opportunity_id': self.id,
                    'company_id': self.lead_company_id.id,
                    'date_order': fields.date.today(),
                    'order_line': order_line_vals
                })
        return res
        

class CrmOrderLine(models.Model):
    _name = "crm.order.line"
    _description = "order line for opportunity"

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.lead_id.company_currency, line.product_uom_qty,
                                            product=line.product_id, partner=line.lead_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True,
        ondelete='restrict',
        check_company=True)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)

    lead_id = fields.Many2one('crm.lead', string='Lead Id', required=True, ondelete='cascade', index=True, copy=False)
    product_uom_qty = fields.Float(
        string="Quantity",
        compute='_compute_product_uom_qty',
        digits='Product Unit of Measure', default=1.0,
        store=True, readonly=False, required=True, precompute=True)
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_product_uom',
        store=True, readonly=False, precompute=True, ondelete='restrict',
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    # Reference field
    name = fields.Text(string='Description',
                              required=True)
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    price_unit = fields.Float(
        string="Unit Price",
        compute='_compute_price_unit',
        digits='Product Price',
        store=True, readonly=False, required=True, precompute=True)
    tax_id = fields.Many2many(
        comodel_name='account.tax',
        string="Taxes",
        compute='_compute_tax_id',
        store=True, readonly=False, precompute=True,
        context={'active_test': False})
    currency_id = fields.Many2one(related='lead_id.company_currency', depends=['lead_id.company_currency'], store=True, 
                                  string='Currency')
    company_id = fields.Many2one(related='lead_id.company_id', string='Company', store=True, index=True)
    order_partner_id = fields.Many2one(related='lead_id.partner_id', store=True, string='Customer', index=True)
    product_custom_attribute_value_ids = fields.One2many('product.attribute.custom.value', 'crm_order_line_id',
                                                         string="Custom Values", copy=True)

    # M2M holding the values of product.attribute with create_variant field set to 'no_variant'
    # It allows keeping track of the extra_price associated to those attribute values and add them to the SO line description
    product_no_variant_attribute_value_ids = fields.Many2many('product.template.attribute.value', string="Extra Values",
                                                              ondelete='restrict')

    # Logistics/Delivery fields
    product_packaging_id = fields.Many2one(
        comodel_name='product.packaging',
        string="Packaging",
        compute='_compute_product_packaging_id',
        store=True, readonly=False, precompute=True,
        domain="[('sales', '=', True), ('product_id','=',product_id)]",
        check_company=True)
    product_packaging_qty = fields.Float(
        string="Packaging Quantity",
        compute='_compute_product_packaging_qty',
        store=True, readonly=False, precompute=True)
    
    def _prepare_order_line(self):
        """Prepare the values to create the new invoice line for a sales order line.

        :param optional_values: any parameter that should be added to the returned invoice line
        :rtype: dict
        """
        self.ensure_one()
        res = {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_uom_qty,
            'product_uom': self.product_uom.id,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_id': [fields.Command.set(self.tax_id.ids)],
        }
        return res

    @api.depends('product_id', 'product_uom_qty', 'product_uom')
    def _compute_product_packaging_id(self):
        for line in self:
            # remove packaging if not match the product
            if line.product_packaging_id.product_id != line.product_id:
                line.product_packaging_id = False
            # Find biggest suitable packaging
            if line.product_id and line.product_uom_qty and line.product_uom:
                line.product_packaging_id = line.product_id.packaging_ids.filtered(
                    'sales')._find_suitable_product_packaging(line.product_uom_qty,
                                                              line.product_uom) or line.product_packaging_id

    @api.depends('product_packaging_id', 'product_uom', 'product_uom_qty')
    def _compute_product_packaging_qty(self):
        for line in self:
            if not line.product_packaging_id:
                line.product_packaging_qty = False
            else:
                packaging_uom = line.product_packaging_id.product_uom_id
                packaging_uom_qty = line.product_uom._compute_quantity(line.product_uom_qty, packaging_uom)
                line.product_packaging_qty = float_round(
                    packaging_uom_qty / line.product_packaging_id.qty,
                    precision_rounding=packaging_uom.rounding)

    @api.depends('product_id', 'product_packaging_qty')
    def _compute_product_uom_qty(self):
        for line in self:
            if not line.product_packaging_id:
                continue
            packaging_uom = line.product_packaging_id.product_uom_id
            qty_per_packaging = line.product_packaging_id.qty
            product_uom_qty = packaging_uom._compute_quantity(
                line.product_packaging_qty * qty_per_packaging, line.product_uom)
            if float_compare(product_uom_qty, line.product_uom_qty, precision_rounding=line.product_uom.rounding) != 0:
                line.product_uom_qty = product_uom_qty
    
    @api.depends('product_id')
    def _compute_product_uom(self):
        for line in self:
            if not line.product_uom or (line.product_id.uom_id.id != line.product_uom.id):
                line.product_uom = line.product_id.uom_id

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            # check if there is already invoiced amount. if so, the price shouldn't change as it might have been
            # manually edited
            if not line.product_uom or not line.product_id or not line.lead_id.partner_id.property_product_pricelist:
                line.price_unit = 0.0
            else:
                price = line.product_id.lst_price#with_company(line.company_id)._get_display_price()
                line.price_unit = line.product_id._get_tax_included_unit_price(
                    line.company_id,
                    line.lead_id.company_currency,
                    fields.date.today(),
                    'sale',
                    fiscal_position=False,
                    product_price_unit=price,
                    product_currency=line.currency_id
                )

    @api.onchange('product_id')
    def product_id_change(self):
        self._update_description()

        product = self.product_id
        if product and product.sale_line_warn != 'no-message':
            if product.sale_line_warn == 'block':
                self.product_id = False
            return {
                'warning': {
                    'title': _("Warning for %s", product.name),
                    'message': product.sale_line_warn_msg,
                }
            }
        
    def _update_description(self):
        if not self.product_id:
            return
        valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
        # remove the is_custom values that don't belong to this template
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.custom_product_template_attribute_value_id not in valid_values:
                self.product_custom_attribute_value_ids -= pacv

        # remove the no_variant attributes that don't belong to this template
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav._origin not in valid_values:
                self.product_no_variant_attribute_value_ids -= ptav

        vals = {}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        lang = get_lang(self.env, self.lead_id.partner_id.lang).code
        product = self.product_id.with_context(
            lang=lang,
        )

        self.update({'name': self.with_context(lang=lang).get_sale_order_line_multiline_description_sale(product)})

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.product_id and self.product_uom:
            self.price_unit = self.product_id.lst_price * self.product_uom_qty
        if self.lead_id.partner_id.property_product_pricelist and self.lead_id.partner_id:
            product = self.product_id.with_context(
                lang=self.lead_id.partner_id.lang,
                partner=self.lead_id.partner_id,
                quantity=self.product_uom_qty,
                date=fields.date.today(),
                pricelist=self.lead_id.partner_id.property_product_pricelist.id,
                uom=self.product_uom.id,
                fiscal_position=False
            )
            self.price_unit = product._get_tax_included_unit_price(
                self.company_id or self.lead_id.company_id,
                self.lead_id.company_currency,
                fields.date.today(),
                'sale',
                product_price_unit=product.lst_price,
                product_currency=self.lead_id.company_currency
            )

    def get_sale_order_line_multiline_description_sale(self, product):
        """ Compute a default multiline description for this sales order line.

        In most cases the product description is enough but sometimes we need to append information that only
        exists on the sale order line itself.
        e.g:
        - custom attributes and attributes that don't create variants, both introduced by the "product configurator"
        - in event_sale we need to know specifically the sales order line as well as the product to generate the name:
          the product is not sufficient because we also need to know the event_id and the event_ticket_id (both which belong to the sale order line).
        """
        return product.get_product_multiline_description_sale() #+ self._get_sale_order_line_multiline_description_variants()

    def _get_sale_order_line_multiline_description_variants(self):
        """When using no_variant attributes or is_custom values, the product
        itself is not sufficient to create the description: we need to add
        information about those special attributes and values.

        :return: the description related to special variant attributes/values
        :rtype: string
        """
        if not self.product_custom_attribute_value_ids and not self.product_no_variant_attribute_value_ids:
            return ""

        name = "\n"

        custom_ptavs = self.product_custom_attribute_value_ids.custom_product_template_attribute_value_id
        no_variant_ptavs = self.product_no_variant_attribute_value_ids._origin

        # display the no_variant attributes, except those that are also
        # displayed by a custom (avoid duplicate description)
        for ptav in (no_variant_ptavs - custom_ptavs):
            name += "\n" + ptav.display_name

        # Sort the values according to _order settings, because it doesn't work for virtual records in onchange
        custom_values = sorted(self.product_custom_attribute_value_ids,
                               key=lambda r: (r.custom_product_template_attribute_value_id.id, r.id))
        # display the is_custom values
        for pacv in custom_values:
            name += "\n" + pacv.display_name

        return name

    @api.depends('product_id')
    def _compute_tax_id(self):
        taxes_by_product_company = defaultdict(lambda: self.env['account.tax'])
        lines_by_company = defaultdict(lambda: self.env['crm.order.line'])
        cached_taxes = {}
        for line in self:
            lines_by_company[line.company_id] += line
        for product in self.product_id:
            for tax in product.taxes_id:
                taxes_by_product_company[(product, tax.company_id)] += tax
        for company, lines in lines_by_company.items():
            for line in lines.with_company(company):
                taxes = taxes_by_product_company[(line.product_id, company)]
                line.tax_id = taxes
                
                
class ProductAttributeCustomValue(models.Model):
    _inherit = "product.attribute.custom.value"

    crm_order_line_id = fields.Many2one('crm.order.line', string="Crm Order Line", required=True, ondelete='cascade')

    _sql_constraints = [
        ('sol_custom_value_unique', 'unique(custom_product_template_attribute_value_id, crm_order_line_id)', "Only one Custom Value is allowed per Attribute Value per Sales Order Line.")
    ]
