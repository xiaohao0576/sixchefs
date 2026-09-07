from odoo import api, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _complete_values_from_session(self, session, values):
        values = dict(values)
        pending_reference = not values.get('pos_reference')
        if pending_reference:
            values['pos_reference'] = '__pending_server_reference__'
            values['tracking_number'] = '__pending_server_tracking_number__'
        values = super()._complete_values_from_session(session, values)
        if pending_reference:
            values.pop('pos_reference', None)
            values.pop('tracking_number', None)
        return values

    @api.model
    def _check_pos_order(self, pos_config, order, device_type, table=None):
        pos_config = pos_config.with_context(defer_server_order_reference=True)
        return super()._check_pos_order(pos_config, order, device_type, table)

    @api.model
    def _process_order(self, order, existing_order):
        order = dict(order)
        if existing_order:
            order.pop('pos_reference', None)
            order.pop('name', None)
        elif order.get('source') not in ('mobile', 'kiosk'):
            order.pop('pos_reference', None)
            order.pop('tracking_number', None)
            order.pop('name', None)
        return super()._process_order(order, existing_order)

    def write(self, vals):
        if vals.get('state') != 'paid':
            return super().write(vals)

        result = True
        for order in self:
            if not order.pos_reference:
                reference, tracking_number = order.config_id._get_next_order_refs()
                result = super(PosOrder, order).write({
                    'pos_reference': reference,
                    'tracking_number': tracking_number,
                }) and result
            result = super(PosOrder, order).write(dict(vals)) and result
        return result

