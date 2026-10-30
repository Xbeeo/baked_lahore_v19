# -*- coding: utf-8 -*-

{
    "name": "Analytic Distribution User Permission",

    'version': '19.0.0.0',

    'summary': """Control Analytic Distribution editing by user""",

    'description': """CNO Pos Analytics Account""",

    'category': 'Analytic Accounting',

    'author': "Cyngro",

    'website': 'https://cyngro.com',

    "depends": ['base','account', 'sale_management','purchase'],

    "data": [
        'views/res_users_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
           ],

}

