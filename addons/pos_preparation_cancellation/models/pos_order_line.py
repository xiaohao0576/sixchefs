from odoo import models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _with_pos_edit_log_context(self, customer_note=None):
        self.ensure_one()
        if customer_note is None:
            customer_note = self.customer_note
        return self.with_context(pos_edit_customer_note=customer_note or "")

    def write(self, vals):
        if (
            len(self) == 1
            and self.order_id.config_id.order_edit_tracking
            and vals.get("qty") is not None
            and vals["qty"] < self.qty
        ):
            return super(
                PosOrderLine,
                self._with_pos_edit_log_context(vals.get("customer_note", self.customer_note)),
            ).write(vals)
        return super().write(vals)

    def unlink(self):
        tracked_lines = self.filtered(
            lambda line: line.order_id.config_id.order_edit_tracking and line.customer_note
        )
        if not tracked_lines:
            return super().unlink()

        result = True
        for line in self:
            result = super(PosOrderLine, line._with_pos_edit_log_context()).unlink() and result
        return result