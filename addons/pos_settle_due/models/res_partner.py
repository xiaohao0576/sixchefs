# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'
    pos_orders_amount_due = fields.Float(string="Sum of customers PoS orders's due amount", compute="_compute_pos_orders_amount_due")
    invoices_amount_due = fields.Float(string="Sum of customers's invoice due amount", compute="_compute_invoices_amount_due")

    def _compute_pos_orders_amount_due(self):
        commercial_partner_ids = {p.id: p.commercial_partner_id.id for p in self}
        # Fetch the total sum of 'customer_due_total' grouped by 'commercial_partner_id'
        pos_orders = self.env['pos.order']._read_group(
            domain=[
                ('commercial_partner_id', 'in', set(commercial_partner_ids.values())),
                ('state', 'in', ['paid', 'done'])
            ],
            groupby=['commercial_partner_id'],
            aggregates=['customer_due_total:sum']
        )

        due_map = {order[0].id: order[1] for order in pos_orders}
        for partner in self:
            partner.pos_orders_amount_due = due_map.get(commercial_partner_ids[partner.id], 0.0)

    def _compute_invoices_amount_due(self):
        commercial_partner_ids = {p.id: p.commercial_partner_id.id for p in self}
        # Fetch the sum of 'pos_amount_unsettled' of unpaid invoices grouped by 'commercial_partner_id'
        invoices = self.env['account.move']._read_group(
            domain=[('commercial_partner_id', 'in', set(commercial_partner_ids.values())),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ('not_paid', 'partial')),
                    ('move_type', 'in', self.env['account.move'].get_sale_types())],
            groupby=['commercial_partner_id'],
            aggregates=['pos_amount_unsettled:sum']
        )

        due_map = {inv[0].id: inv[1] for inv in invoices}
        for partner in self:
            partner.invoices_amount_due = due_map.get(commercial_partner_ids[partner.id], 0.0)
