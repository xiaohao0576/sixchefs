from datetime import datetime

from odoo import models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _get_next_order_refs(self, device_identifier='0'):
        self.ensure_one()
        if self.env.context.get('defer_server_order_reference'):
            return False, False
        next_number = self.order_backend_seq_id._next()
        year = datetime.now().year
        reference = f'{year}-{self.id:02d}-{int(next_number):06d}'
        tracking_number = f'{int(next_number) % 1000:03d}'
        return reference, tracking_number
