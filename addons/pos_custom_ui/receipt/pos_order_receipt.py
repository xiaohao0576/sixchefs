from odoo import models


class PosOrderReceipt(models.AbstractModel):
    _inherit = 'pos.order.receipt'

    def order_receipt_generate_data(self, basic_receipt=False):
        data = super().order_receipt_generate_data(basic_receipt)
        product_templates = self.lines.product_id.product_tmpl_id
        language_names_by_template_id = {
            product.id: {
                'name_en': product.name_en,
                'name_km': product.name_km,
                'name_cn': product.name_cn,
            }
            for product in product_templates
        }

        for line in data['lines']:
            product_template = self.env['product.product'].browse(line['product_id']).product_tmpl_id
            language_names = language_names_by_template_id[product_template.id]
            line.update(language_names)
            line['product_data'].update(language_names)

        return data
