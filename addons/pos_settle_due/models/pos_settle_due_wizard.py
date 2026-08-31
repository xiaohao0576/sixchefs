import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command


class PosSettleDueWizard(models.TransientModel):
    _name = 'pos.settle.due.wizard'
    _description = 'POS Settle Due Wizard'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)
    session_id = fields.Many2one(
        'pos.session',
        string='Session',
        required=True,
        domain="[('state', '=', 'opened'), ('company_id', '=', company_id)]",
    )
    company_id = fields.Many2one('res.company', related='session_id.company_id', readonly=True)
    currency_id = fields.Many2one('res.currency', related='session_id.currency_id', readonly=True)
    selected_order_ids = fields.Many2many(
        'pos.order',
        string='Orders to Settle',
        domain="[('state', 'in', ['paid', 'done']), ('session_id.state', '=', 'closed'), ('customer_due_total', '>', 0), ('commercial_partner_id', '=', partner_id), ('currency_id', '=', currency_id)]",
    )
    selected_due_total = fields.Monetary(
        string='Selected Due Total',
        compute='_compute_selected_due_total',
        currency_field='currency_id',
    )
    amount = fields.Monetary(string='Amount Received', required=True, currency_field='currency_id')
    adjustment_amount = fields.Monetary(
        string='Discount',
        compute='_compute_adjustment_amount',
        currency_field='currency_id',
    )
    available_payment_method_ids = fields.Many2many(
        'pos.payment.method',
        compute='_compute_available_payment_method_ids',
        string='Available Payment Methods',
    )
    payment_method_id = fields.Many2one(
        'pos.payment.method',
        string='Payment Method',
        required=True,
        domain="[('id', 'in', available_payment_method_ids)]",
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        selected_order_ids = self.env.context.get('default_selected_order_ids') or []
        if not values.get('selected_order_ids') and selected_order_ids:
            values['selected_order_ids'] = [Command.set(selected_order_ids)]
        if not values.get('session_id') and selected_order_ids:
            orders = self.env['pos.order'].browse(selected_order_ids)
            if orders:
                values['session_id'] = orders._get_open_settle_due_session().id
        return values

    @api.depends('selected_order_ids.customer_due_total')
    def _compute_selected_due_total(self):
        for wizard in self:
            wizard.selected_due_total = sum(wizard.selected_order_ids.mapped('customer_due_total'))

    @api.depends('amount', 'selected_due_total')
    def _compute_adjustment_amount(self):
        for wizard in self:
            wizard.adjustment_amount = wizard.amount - wizard.selected_due_total

    @api.depends('session_id')
    def _compute_available_payment_method_ids(self):
        for wizard in self:
            methods = wizard.session_id.config_id.payment_method_ids.filtered(lambda method: method.type != 'pay_later')
            wizard.available_payment_method_ids = methods

    @api.onchange('selected_order_ids')
    def _onchange_selected_order_ids(self):
        for wizard in self:
            if not wizard.selected_order_ids:
                wizard.amount = 0
                continue
            partners = wizard.selected_order_ids.mapped('commercial_partner_id')
            if len(partners) != 1:
                raise ValidationError(_('All selected orders must belong to the same customer.'))
            wizard.partner_id = partners[0]
            wizard.amount = wizard.selected_due_total

    @api.onchange('amount', 'selected_due_total')
    def _onchange_amount_warning(self):
        for wizard in self:
            if wizard.amount and wizard.selected_due_total and wizard.amount != wizard.selected_due_total:
                adjustment = wizard.amount - wizard.selected_due_total
                return {
                    'warning': {
                        'title': _('Settlement Difference'),
                        'message': _(
                            'A settlement difference of %(difference).2f will be posted as a discount adjustment line.',
                            difference=adjustment,
                        ),
                    }
                }

    @api.constrains('amount', 'selected_order_ids')
    def _check_amount_bounds(self):
        for wizard in self:
            if wizard.amount <= 0:
                raise ValidationError(_('Amount must be greater than zero.'))
            if wizard.amount > wizard.selected_due_total:
                raise ValidationError(_('Amount cannot exceed the selected due total.'))

    @api.constrains('selected_order_ids', 'partner_id')
    def _check_selected_orders(self):
        for wizard in self:
            if not wizard.selected_order_ids:
                raise ValidationError(_('Please select at least one order to settle.'))
            partners = wizard.selected_order_ids.mapped('commercial_partner_id')
            if len(partners) != 1:
                raise ValidationError(_('All selected orders must belong to the same customer.'))
            if wizard.partner_id and partners[0] != wizard.partner_id:
                raise ValidationError(_('Selected orders do not match the chosen customer.'))

    def action_confirm(self):
        self.ensure_one()
        orders = self.selected_order_ids._validate_orders_for_settle_due()
        if orders.company_id != self.session_id.company_id:
            raise UserError(_('The selected orders and POS session must belong to the same company.'))
        if any(order.currency_id != self.session_id.currency_id for order in orders):
            raise UserError(_('The selected orders and POS session must use the same currency.'))

        if self.session_id.state != 'opened':
            raise UserError(_('The selected POS session is not open anymore.'))

        if self.payment_method_id.type == 'pay_later':
            raise UserError(_('Please choose a payment method other than Customer Account.'))

        if self.payment_method_id not in self.session_id.config_id.payment_method_ids:
            raise UserError(_('The selected payment method is not available in the POS session config.'))

        pay_later_method = self.session_id.config_id.payment_method_ids.filtered(
            lambda method: method.type == 'pay_later'
        )[:1]
        if not pay_later_method:
            raise UserError(_('The POS config must contain a Customer Account payment method.'))

        settle_product = self.session_id.config_id.settle_due_product_id
        if not settle_product:
            raise UserError(_('Please configure a Settle Due product on this POS config.'))

        adjustment_product = self.env.ref('pos_discount.product_product_consumable', raise_if_not_found=False)

        line_commands = []
        for order in self.selected_order_ids:
            line_commands.append(Command.create({
                'product_id': settle_product.id,
                'qty': 0,
                'price_unit': order.customer_due_total,
                'price_subtotal': 0,
                'price_subtotal_incl': 0,
                'discount': 0,
                'price_extra': 0,
                'price_type': 'manual',
                'refunded_qty': 0,
                'note': json.dumps([{'text': _('Settled source order: %(order_name)s', order_name=order.name), 'colorIndex': 0}]),
                'tax_ids': [Command.clear()],
                'settled_order_id': order.id,
            }))

        if self.adjustment_amount:
            if not adjustment_product:
                raise UserError(_('Discount product pos_discount.product_product_consumable was not found.'))
            line_commands.append(Command.create({
                'product_id': adjustment_product.id,
                'qty': 1,
                'price_unit': self.adjustment_amount,
                'price_subtotal': self.adjustment_amount,
                'price_subtotal_incl': self.adjustment_amount,
                'discount': 0,
                'price_extra': 0,
                'price_type': 'manual',
                'refunded_qty': 0,
                'tax_ids': [Command.clear()],
            }))

        settlement_order = self.env['pos.order'].create({
            'session_id': self.session_id.id,
            'config_id': self.session_id.config_id.id,
            'company_id': self.session_id.company_id.id,
            'partner_id': self.partner_id.id,
            'amount_paid': 0,
            'amount_return': 0,
            'amount_tax': 0,
            'amount_total': 0,
            'lines': line_commands,
        })

        settlement_order.lines._onchange_amount_line_all()
        settlement_order._compute_prices()

        settlement_order.add_payment({
            'name': _('Settlement Payment'),
            'pos_order_id': settlement_order.id,
            'amount': self.amount,
            'payment_date': fields.Datetime.now(),
            'payment_method_id': self.payment_method_id.id,
        })
        settlement_order.add_payment({
            'name': _('Customer Account Offset'),
            'pos_order_id': settlement_order.id,
            'amount': -self.selected_due_total,
            'payment_date': fields.Datetime.now(),
            'payment_method_id': pay_later_method.id,
        })

        settlement_order.action_pos_order_paid()

        settlement_order_link = settlement_order._get_html_link(title=settlement_order.name)
        for source_order in self.selected_order_ids:
            source_order_link = source_order._get_html_link(title=source_order.name)
            source_order.message_post(body=_('Settlement order link: ') + settlement_order_link)
            settlement_order.message_post(body=_('Source order link: ') + source_order_link)

        return {
            'name': _('Settlement Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_mode': 'form',
            'res_id': settlement_order.id,
            'target': 'current',
        }
