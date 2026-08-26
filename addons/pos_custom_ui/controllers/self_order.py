from odoo.addons.pos_self_order.controllers.orders import PosSelfOrderController


class PosCustomSelfOrderController(PosSelfOrderController):
    def _verify_authorization(self, access_token, table_identifier, order):
        pos_config, table = super()._verify_authorization(
            access_token, table_identifier, order
        )
        if order.get("disable_indexeddb"):
            pos_config = pos_config.with_context(disable_self_order_preparation=True)
        return pos_config, table