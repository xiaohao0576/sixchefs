from markupsafe import Markup

from odoo import models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _prepare_pos_log(self, body):
        body = super()._prepare_pos_log(body)
        customer_note = self.env.context.get("pos_edit_customer_note")
        if customer_note:
            body += Markup("<br/>Customer Note: %(customer_note)s") % {
                "customer_note": customer_note,
            }
        return body