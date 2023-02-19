# -*- coding: utf-8 -*-
{
    'name': "test_crm",

    'summary': """
        Allcore testing module
    """,

    'description': """
        Allcore testing module description
    """,

    'author': "Paolo Cappelletto",
    'website': "https://www.soluzionetasse.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'sale_management', 
        'crm'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/company.xml', 
        'data/salesteam.xml', 
        'data/stages.xml',
        'views/quick_create_opportunity_form_ext.xml'
        # 'views/templates.xml',
    ],

    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False
}

# COMMANDS
# odoo -u test_crm -d crm-test --stop-after-init
# odoo -u all -d pippotest --stop-after-init
# upgrade on odoo.sh
# odoo-bin -u test_crm -d [] --stop-after-init
