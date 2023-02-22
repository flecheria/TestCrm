# -*- coding: utf-8 -*-
"""
Imported required files.
"""

from odoo.tests import common
from datetime import date


class TestForCrm(common.TransactionCase):

    def setUp(self):
        """
        This function will set the required data.
        """

    def test_favourite_contact_with_both_user(self):
        """
        This function will add mitchell-admin and marc-demo to the favourite contacts.
        """

        product1 = self.env['product.product'].create({
            'name':'test_product_1',
            'sale_ok':True,
            'detailed_type':'consu',
            'lst_price':9.0
        })

        product2 = self.env['product.product'].create({
            'name': 'test_product_2',
            'sale_ok': True,
            'detailed_type':'consu',
            'lst_price': 20
        })

        partner = self.env['res.partner'].create({
            'name': 'Paolo'
        })

        crm_lead = self.env['crm.lead'].create({
            'partner_id': partner.id,
            'name': partner.name + 'Lead',
            'market_id': self.env.ref('base.it').id,
            'lead_company_id': self.env.ref('base.main_company').id
        })

        crm_order_line_1 = self.env['crm.order.line'].create({
            'product_id':product1.id,
            'name': product1.display_name,
            'lead_id':crm_lead.id
        })
        crm_order_line_2 = self.env['crm.order.line'].create({
            'product_id': product2.id,
            'name': product1.display_name,
            'lead_id': crm_lead.id
        })
        # Test for one won lead
        stage_team1_won2 = self.env['crm.stage'].create({
            'name': 'Won2',
            'sequence': 75,
            'team_id': False,
            'is_won': True,
        })

        crm_lead.stage_id = stage_team1_won2
        self.assertTrue(crm_lead.stage_id, stage_team1_won2)

        sale_order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'opportunity_id': crm_lead.id,
            'company_id': self.env.ref('base.main_company').id,
            'date_order': date.today(),
        })

        order_line_1 = self.env['sale.order.line'].create({
            'product_id': product1.id,
            'name': product1.display_name,
            'order_id': sale_order.id
        })
        order_line_2 = self.env['sale.order.line'].create({
            'product_id': product2.id,
            'name': product1.display_name,
            'order_id': sale_order.id
        })
        self.assertTrue(crm_lead.id)
        self.assertTrue(crm_lead.order_ids.ids)
        self.assertNotEqual(crm_lead.name,crm_lead.order_ids[0].name)
