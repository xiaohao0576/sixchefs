from odoo import models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _should_send_to_preparation(self):
        return False