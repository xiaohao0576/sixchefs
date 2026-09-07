{
    'name': 'POS Server Order Sequence',
    'version': '1.0.0',
    'author': 'Sixchefs',
    'category': 'Point of Sale',
    'summary': 'Generate POS order references centrally on the server',
    'depends': ['point_of_sale', 'pos_self_order'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_server_order_sequence/static/src/app/services/pos_store.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
