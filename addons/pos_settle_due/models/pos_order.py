from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PosOrder(models.Model):
    _inherit = 'pos.order'

    customer_due_total = fields.Monetary(string="Due", compute="_compute_customer_due_total", store=True, currency_field="currency_id")
    init_customer_due_total = fields.Monetary(string="Initial due (before any settlement)", currency_field="currency_id")
    settled_order_line_ids = fields.One2many("pos.order.line", "settled_order_id", string="Settled Order Lines")
    settled_orders_count = fields.Integer(string="Number of settled orders", compute='_compute_settled_orders_count', store=True)
    commercial_partner_id = fields.Many2one(comodel_name="res.partner", related="partner_id.commercial_partner_id", readonly=True, store=True)

    @api.depends('payment_ids.amount', 'payment_ids.payment_method_id', 'settled_order_line_ids.price_unit', 'is_invoiced', 'partner_id')
    def _compute_customer_due_total(self):
        for order in self:
            if not order.partner_id or order.is_invoiced:
                order.customer_due_total = 0
                order.init_customer_due_total = 0
                continue

            order_due = order.currency_id.round(sum(
                order.payment_ids.filtered(
                    lambda payment: payment.amount > 0 and payment.payment_method_id.type == 'pay_later'
                ).mapped('amount')
            ))
            order_settled = order.currency_id.round(sum(order.settled_order_line_ids.mapped('price_unit')))
            remaining_due = order.currency_id.round(order_due - order_settled)
            order.init_customer_due_total = order_due
            order.customer_due_total = remaining_due if remaining_due > 0 else 0

    @api.depends('settled_order_line_ids')
    def _compute_settled_orders_count(self):
        for order in self:
            order.settled_orders_count = len(order.settled_order_line_ids)

    def action_view_settled_orders(self):
        return {
            'name': _('Settled Orders'),
            'view_mode': 'list,form',
            'res_model': 'pos.order',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.mapped('settled_order_line_ids.order_id').ids)],
        }

    def _get_payments(self):
        payments = super()._get_payments()
        payments += self.settled_order_line_ids.order_id.payment_ids.sudo().with_company(self.company_id)
        return payments

    def _get_open_settle_due_session(self):
        companies = self.mapped('company_id')
        if len(companies) != 1:
            raise UserError(_('You can only settle due orders from the same company.'))

        session = self.env['pos.session'].search([
            ('company_id', '=', companies.id),
            ('state', '=', 'opened'),
        ], limit=1)
        if not session:
            raise UserError(_('No POS session is currently open. Open a session before settling dues.'))
        return session

    def _validate_orders_for_settle_due(self):
        if not self:
            raise UserError(_('Please select at least one POS order to settle.'))

        orders = self.filtered(
            lambda order: order.state in ('paid', 'done')
            and order.session_id.state == 'closed'
            and order.customer_due_total > 0
        )
        if not orders:
            raise UserError(_('Only POS orders from closed sessions with remaining due can be settled.'))

        if len(orders.mapped('commercial_partner_id')) != 1:
            raise UserError(_('All selected orders must belong to the same customer.'))
        return orders

    def action_open_settle_due_wizard(self):
        orders = self._validate_orders_for_settle_due()
        session = orders._get_open_settle_due_session()
        return {
            'name': _('Settle Due'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.settle.due.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': orders[0].commercial_partner_id.id,
                'default_session_id': session.id,
                'default_selected_order_ids': orders.ids,
                'default_amount': sum(orders.mapped('customer_due_total')),
            },
        }
