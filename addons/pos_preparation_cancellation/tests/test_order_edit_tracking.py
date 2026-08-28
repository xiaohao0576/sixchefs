from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import CommonPosTest


@tagged("post_install", "-at_install")
class TestOrderEditTrackingCustomerNote(CommonPosTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config_usd.order_edit_tracking = True
        cls.order, _refund = cls.create_backend_pos_order(
            cls,
            {
                "line_data": [
                    {
                        "product_id": cls.ten_dollars_with_10_incl.product_variant_id.id,
                        "qty": 3,
                        "customer_note": "质量问题",
                    },
                    {
                        "product_id": cls.twenty_dollars_with_10_incl.product_variant_id.id,
                        "qty": 2,
                        "customer_note": "顾客原因",
                    },
                ],
            },
        )

    def test_quantity_decrease_log_includes_customer_note(self):
        line = self.order.lines[0]

        line.write({"qty": 2, "customer_note": "退菜原因：质量问题"})

        message = self.order.message_ids[0]
        self.assertIn("Ordered quantity", message.body)
        self.assertIn("Customer Note: 退菜原因：质量问题", message.body)

    def test_deleted_line_log_includes_customer_note(self):
        line = self.order.lines[1]

        line.unlink()

        message = self.order.message_ids[0]
        self.assertIn("Deleted line", message.body)
        self.assertIn("Customer Note: 顾客原因", message.body)