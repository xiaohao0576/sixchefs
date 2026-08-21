{
    'name': 'POS Custom UI',
    'version': '1.0.0',
    'category': 'Point of Sale',
    'summary': 'Custom POS UI product language fields',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_custom_ui/static/src/app/utils/printer/generate_printer_data.js',
            'pos_custom_ui/static/src/app/components/product_card/product_card.xml',
            'pos_custom_ui/static/src/app/components/orderline/orderline.xml',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}