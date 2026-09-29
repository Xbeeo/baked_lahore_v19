# -*- coding: utf-8 -*-

{
    "name": "CNO Baked Custom",

    'version': '19.0.0.0',

    'summary': """CNO Baked Custom""",

    'description': """CNO Baked Custom""",

    'category': 'All',

    'author': "Musadiq Fiaz",

    'website': 'https://cyngro.com',

    "depends": ['base','stock','analytic','product','account','mrp','point_of_sale'],

    "data": [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence_data.xml',
        'views/product_template_views.xml',
        'views/product_variant_views.xml',
        'views/stock_views.xml',
        'views/pos_payment_method_views.xml',
        'views/expenses_voucher_views.xml',
        'views/accounting_head_views.xml',
        'views/cogs_basis_views.xml',
        'views/profit_classification_views.xml',
        'views/stock_quant_view.xml',
        'views/account_analytic_plan_view.xml',
        'views/account_journal_views.xml',
        'views/stock_scrap_views.xml',
        # 'views/mrp_production_views.xml',
           ],

}
