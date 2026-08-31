import json

import odoo
from odoo.fields import Command
from odoo.addons.point_of_sale.tests.common import TestPoSCommon
from odoo.exceptions import UserError


@odoo.tests.tagged('post_install', '-at_install', 'pos_settle_due')
class TestSettleDueWizard(TestPoSCommon):

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.open_new_session()

    def _close_source_session_and_open_settlement_session(self, config=None):
        source_session = self.pos_session
        source_session.close_session_from_ui()
        self.assertEqual(source_session.state, 'closed')
        self.config = config or self.basic_config
        self.open_new_session()
        return source_session

    def test_settle_due_with_small_delta_creates_adjustment_and_full_offset(self):
        product = self.create_product(
            name='Settle Due Regression Product',
            category=self.env.ref('product.product_category_services'),
            lst_price=20.01,
            tax_ids=[],
        )

        order_data = self.create_ui_order_data(
            pos_order_lines_ui_args=[(product, 1)],
            customer=self.customer,
            is_invoiced=False,
            payments=[(self.pay_later_pm, 20.01)],
        )
        order_id = self.env['pos.order'].sync_from_ui([order_data])['pos.order'][0]['id']
        source_order = self.env['pos.order'].browse(order_id)

        self.assertAlmostEqual(source_order.customer_due_total, 20.01, places=2)
        self._close_source_session_and_open_settlement_session()

        action = source_order.action_open_settle_due_wizard()
        wizard = self.env['pos.settle.due.wizard'].with_context(action['context']).create({
            'partner_id': source_order.commercial_partner_id.id,
            'session_id': self.pos_session.id,
            'selected_order_ids': [Command.set(source_order.ids)],
            'payment_method_id': self.cash_pm1.id,
            'amount': 20.00,
        })

        result = wizard.action_confirm()
        settlement_order = self.env['pos.order'].browse(result['res_id'])

        settle_line = settlement_order.lines.filtered(lambda line: line.settled_order_id == source_order)
        self.assertEqual(len(settle_line), 1)
        self.assertAlmostEqual(settle_line.qty, 0.0, places=2)
        self.assertAlmostEqual(settle_line.price_unit, 20.01, places=2)
        self.assertAlmostEqual(settle_line.price_subtotal, 0.0, places=2)

        discount_product = self.env.ref('pos_discount.product_product_consumable')
        adjustment_line = settlement_order.lines.filtered(lambda line: line.product_id == discount_product)
        self.assertEqual(len(adjustment_line), 1)
        self.assertAlmostEqual(adjustment_line.qty, 1.0, places=2)
        self.assertAlmostEqual(adjustment_line.price_unit, -0.01, places=2)
        self.assertAlmostEqual(adjustment_line.price_subtotal, -0.01, places=2)

        cash_payment = settlement_order.payment_ids.filtered(lambda p: p.payment_method_id == self.cash_pm1)
        self.assertEqual(len(cash_payment), 1)
        self.assertAlmostEqual(cash_payment.amount, 20.00, places=2)

        pay_later_payment = settlement_order.payment_ids.filtered(
            lambda payment: payment.payment_method_id.type == 'pay_later'
        )
        self.assertEqual(len(pay_later_payment), 1)
        self.assertAlmostEqual(pay_later_payment.amount, -20.01, places=2)

    def test_settle_due_with_exact_amount_creates_no_discount_adjustment(self):
        product = self.create_product(
            name='Settle Due Exact Amount Product',
            category=self.env.ref('product.product_category_services'),
            lst_price=20.01,
            tax_ids=[],
        )

        order_data = self.create_ui_order_data(
            pos_order_lines_ui_args=[(product, 1)],
            customer=self.customer,
            is_invoiced=False,
            payments=[(self.pay_later_pm, 20.01)],
        )
        order_id = self.env['pos.order'].sync_from_ui([order_data])['pos.order'][0]['id']
        source_order = self.env['pos.order'].browse(order_id)

        self.assertAlmostEqual(source_order.customer_due_total, 20.01, places=2)
        self._close_source_session_and_open_settlement_session()

        action = source_order.action_open_settle_due_wizard()
        wizard = self.env['pos.settle.due.wizard'].with_context(action['context']).create({
            'partner_id': source_order.commercial_partner_id.id,
            'session_id': self.pos_session.id,
            'selected_order_ids': [Command.set(source_order.ids)],
            'payment_method_id': self.cash_pm1.id,
            'amount': 20.01,
        })

        result = wizard.action_confirm()
        settlement_order = self.env['pos.order'].browse(result['res_id'])

        settle_line = settlement_order.lines.filtered(lambda line: line.settled_order_id == source_order)
        self.assertEqual(len(settle_line), 1)
        self.assertAlmostEqual(settle_line.qty, 0.0, places=2)
        self.assertAlmostEqual(settle_line.price_unit, 20.01, places=2)
        self.assertAlmostEqual(settle_line.price_subtotal, 0.0, places=2)

        discount_product = self.env.ref('pos_discount.product_product_consumable')
        adjustment_line = settlement_order.lines.filtered(lambda line: line.product_id == discount_product)
        self.assertEqual(len(adjustment_line), 0)

        cash_payment = settlement_order.payment_ids.filtered(lambda p: p.payment_method_id == self.cash_pm1)
        self.assertEqual(len(cash_payment), 1)
        self.assertAlmostEqual(cash_payment.amount, 20.01, places=2)

        pay_later_payment = settlement_order.payment_ids.filtered(
            lambda payment: payment.payment_method_id.type == 'pay_later'
        )
        self.assertEqual(len(pay_later_payment), 1)
        self.assertAlmostEqual(pay_later_payment.amount, -20.01, places=2)

    def test_settle_due_multiple_orders_keeps_single_discount_and_line_notes(self):
        product_a = self.create_product(
            name='Settle Due Multi A',
            category=self.env.ref('product.product_category_services'),
            lst_price=10.00,
            tax_ids=[],
        )
        product_b = self.create_product(
            name='Settle Due Multi B',
            category=self.env.ref('product.product_category_services'),
            lst_price=10.01,
            tax_ids=[],
        )

        order_data_a = self.create_ui_order_data(
            pos_order_lines_ui_args=[(product_a, 1)],
            customer=self.customer,
            is_invoiced=False,
            payments=[(self.pay_later_pm, 10.00)],
        )
        order_data_b = self.create_ui_order_data(
            pos_order_lines_ui_args=[(product_b, 1)],
            customer=self.customer,
            is_invoiced=False,
            payments=[(self.pay_later_pm, 10.01)],
        )
        order_id_a = self.env['pos.order'].sync_from_ui([order_data_a])['pos.order'][0]['id']
        order_id_b = self.env['pos.order'].sync_from_ui([order_data_b])['pos.order'][0]['id']
        source_order_a = self.env['pos.order'].browse(order_id_a)
        source_order_b = self.env['pos.order'].browse(order_id_b)

        self.assertAlmostEqual(source_order_a.customer_due_total, 10.00, places=2)
        self.assertAlmostEqual(source_order_b.customer_due_total, 10.01, places=2)
        self._close_source_session_and_open_settlement_session()

        wizard = self.env['pos.settle.due.wizard'].create({
            'partner_id': self.customer.commercial_partner_id.id,
            'session_id': self.pos_session.id,
            'selected_order_ids': [Command.set([source_order_a.id, source_order_b.id])],
            'payment_method_id': self.cash_pm1.id,
            'amount': 20.00,
        })

        result = wizard.action_confirm()
        settlement_order = self.env['pos.order'].browse(result['res_id'])

        settle_lines = settlement_order.lines.filtered(
            lambda line: line.settled_order_id in (source_order_a | source_order_b)
        )
        self.assertEqual(len(settle_lines), 2)

        line_by_source = {line.settled_order_id.id: line for line in settle_lines}
        self.assertAlmostEqual(line_by_source[source_order_a.id].price_unit, 10.00, places=2)
        self.assertAlmostEqual(line_by_source[source_order_b.id].price_unit, 10.01, places=2)
        self.assertAlmostEqual(line_by_source[source_order_a.id].qty, 0.0, places=2)
        self.assertAlmostEqual(line_by_source[source_order_b.id].qty, 0.0, places=2)
        self.assertEqual(
            json.loads(line_by_source[source_order_a.id].note),
            [{'text': f'Settled source order: {source_order_a.name}', 'colorIndex': 0}],
        )
        self.assertEqual(
            json.loads(line_by_source[source_order_b.id].note),
            [{'text': f'Settled source order: {source_order_b.name}', 'colorIndex': 0}],
        )

        discount_product = self.env.ref('pos_discount.product_product_consumable')
        adjustment_line = settlement_order.lines.filtered(lambda line: line.product_id == discount_product)
        self.assertEqual(len(adjustment_line), 1)
        self.assertAlmostEqual(adjustment_line.price_unit, -0.01, places=2)

        source_a_bodies = source_order_a.message_ids.mapped('body')
        source_b_bodies = source_order_b.message_ids.mapped('body')
        settlement_bodies = settlement_order.message_ids.mapped('body')

        self.assertTrue(any('Settlement order link:' in body for body in source_a_bodies))
        self.assertTrue(any(settlement_order.name in body for body in source_a_bodies))
        self.assertTrue(any('Settlement order link:' in body for body in source_b_bodies))
        self.assertTrue(any(settlement_order.name in body for body in source_b_bodies))
        self.assertTrue(any('Source order link:' in body for body in settlement_bodies))
        self.assertTrue(any(source_order_a.name in body for body in settlement_bodies))
        self.assertTrue(any(source_order_b.name in body for body in settlement_bodies))

    def test_settle_due_rejects_orders_from_another_company(self):
        product = self.create_product(
            name='Settle Due Cross Company Product',
            category=self.env.ref('product.product_category_services'),
            lst_price=20.00,
            tax_ids=[],
        )
        order_data = self.create_ui_order_data(
            pos_order_lines_ui_args=[(product, 1)],
            customer=self.customer,
            is_invoiced=False,
            payments=[(self.pay_later_pm, 20.00)],
        )
        order_id = self.env['pos.order'].sync_from_ui([order_data])['pos.order'][0]['id']
        source_order = self.env['pos.order'].browse(order_id)
        self._close_source_session_and_open_settlement_session()
        wizard = self.env['pos.settle.due.wizard'].create({
            'partner_id': source_order.commercial_partner_id.id,
            'session_id': self.pos_session.id,
            'selected_order_ids': [Command.set(source_order.ids)],
            'payment_method_id': self.cash_pm1.id,
            'amount': 20.00,
        })

        other_company = self.setup_other_company()['company']
        self.env.user.company_ids |= other_company
        source_order.company_id = other_company

        with self.assertRaisesRegex(UserError, 'must belong to the same company'):
            wizard.action_confirm()

    def test_settle_due_rejects_order_from_open_session(self):
        product = self.create_product(
            name='Settle Due Open Session Product',
            category=self.env.ref('product.product_category_services'),
            lst_price=20.00,
            tax_ids=[],
        )
        order_data = self.create_ui_order_data(
            pos_order_lines_ui_args=[(product, 1)],
            customer=self.customer,
            is_invoiced=False,
            payments=[(self.pay_later_pm, 20.00)],
        )
        order_id = self.env['pos.order'].sync_from_ui([order_data])['pos.order'][0]['id']
        source_order = self.env['pos.order'].browse(order_id)

        with self.assertRaisesRegex(UserError, 'closed sessions'):
            source_order.action_open_settle_due_wizard()

    def test_settle_due_rejects_different_currency(self):
        product = self.create_product(
            name='Settle Due Currency Product',
            category=self.env.ref('product.product_category_services'),
            lst_price=20.00,
            tax_ids=[],
        )
        order_data = self.create_ui_order_data(
            pos_order_lines_ui_args=[(product, 1)],
            customer=self.customer,
            is_invoiced=False,
            payments=[(self.pay_later_pm, 20.00)],
        )
        order_id = self.env['pos.order'].sync_from_ui([order_data])['pos.order'][0]['id']
        source_order = self.env['pos.order'].browse(order_id)
        self._close_source_session_and_open_settlement_session(self.other_currency_config)
        wizard = self.env['pos.settle.due.wizard'].create({
            'partner_id': source_order.commercial_partner_id.id,
            'session_id': self.pos_session.id,
            'selected_order_ids': [Command.set(source_order.ids)],
            'payment_method_id': self.cash_pm2.id,
            'amount': 20.00,
        })

        with self.assertRaisesRegex(UserError, 'must use the same currency'):
            wizard.action_confirm()
