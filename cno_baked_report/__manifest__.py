# -*- coding: utf-8 -*-
{
    "name": "CNO Baked Report",

    'version': '19.0.0.0',

    'summary': """CNO Baked Report""",

    'description': """CNO Baked Report""",

    'category': 'Baked',

    'author': "Cyngro",

    'website': 'https://cyngro.com',

    "depends": ['base', 'report_xlsx', 'cno_baked_custom'],

    "data": [
        'security/ir.model.access.csv',
        'report/report_action.xml',
        'report/expenses_voucher_report_template.xml',
        'report/stock_scrap_report_template.xml',
        'report/purchase_ledger_report.xml',
        'report/purchase_ledger_report_template.xml',
        'report/report_payment_receipt_templates.xml',
        'wizards/purchase_ledger_wizard_view.xml',
        'wizards/sale_analysis_report_wizard.xml',
        'wizards/quant_report_wizard_view.xml',
        # 'wizards/stock_move_analytic_report_wizard_views.xml',
        'wizards/expense_voucher_report_wizard_view.xml',
        'wizards/consolidated_inventory_report_view.xml',
        'wizards/scrap_report_wizard_views.xml',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,

}
