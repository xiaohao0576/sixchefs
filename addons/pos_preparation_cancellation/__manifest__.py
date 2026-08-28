{
    "name": "POS Preparation Cancellation",
    "summary": "Cancel prepared items with a reason from the Point of Sale",
    "version": "1.0.2",
    "category": "Sales/Point of Sale",
    "author": "HoganTech",
    "depends": ["point_of_sale", "pos_restaurant"],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_preparation_cancellation/static/src/**/*",
        ],
        "web.assets_unit_tests": [
            "pos_preparation_cancellation/static/tests/unit/**/*",
        ],
    },
    "license": "LGPL-3",
    "installable": True,
}