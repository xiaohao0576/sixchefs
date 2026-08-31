# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Point of Sale Settle Due',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': "Settle partner's due in the POS UI.",
    'depends': ['point_of_sale', 'pos_discount'],
    'installable': True,
    'auto_install': False,
    'author': 'Hogan',
    'license': 'LGPL-3',
    'data': [
        'security/ir.access.csv',
        'views/pos_order_views.xml',
        'views/pos_settle_due_wizard_views.xml',
        'views/account_move_views.xml',
        'data/pos_settle_due_data.xml',
    ],
}
