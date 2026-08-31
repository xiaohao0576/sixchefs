{
    'name': 'POS Pricelist as Discount',
    'category': 'Sales/Point of Sale',
    'summary': 'Apply selected POS pricelists as order line discounts',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_pricelist_as_discount/static/src/**/*',
        ],
    },
    'license': 'LGPL-3',
}