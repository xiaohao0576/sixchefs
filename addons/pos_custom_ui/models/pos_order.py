from odoo import models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _should_send_to_preparation(self):
        if self.env.context.get("disable_self_order_preparation"):
            return False
        return super()._should_send_to_preparation()