from datetime import datetime

from odoo.tests.common import TransactionCase


class TestPosServerOrderSequence(TransactionCase):
    def test_draft_order_does_not_get_formal_reference(self):
        config = self.env['pos.config'].create({
            'name': 'Deferred Sequence POS',
            'company_id': self.env.company.id,
        })
        session = self.env['pos.session'].create({
            'config_id': config.id,
            'user_id': self.env.user.id,
        })

        values = self.env['pos.order']._complete_values_from_session(
            session,
            {'session_id': session.id, 'source': 'pos'},
        )

        self.assertFalse(values.get('pos_reference'))
        self.assertFalse(values.get('tracking_number'))

    def test_order_reference_format_uses_backend_sequence(self):
        config = self.env['pos.config'].create({
            'name': 'Server Sequence POS',
            'company_id': self.env.company.id,
        })

        first_reference, first_tracking = config._get_next_order_refs()
        second_reference, second_tracking = config._get_next_order_refs()

        year = datetime.now().year
        first_number = int(first_reference.rsplit('-', 1)[1])
        second_number = int(second_reference.rsplit('-', 1)[1])
        self.assertEqual(first_reference, f'{year}-{config.id:02d}-{first_number:06d}')
        self.assertEqual(second_reference, f'{year}-{config.id:02d}-{second_number:06d}')
        self.assertEqual(second_number, first_number + 1)
        self.assertEqual(first_tracking, f'{first_number % 1000:03d}')
        self.assertEqual(second_tracking, f'{second_number % 1000:03d}')
