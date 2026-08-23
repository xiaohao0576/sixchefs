from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    name_en = fields.Char(string='English Name', compute='_compute_pos_custom_names')
    name_km = fields.Char(string='Khmer Name', compute='_compute_pos_custom_names')
    name_cn = fields.Char(string='Chinese Name', compute='_compute_pos_custom_names')

    @api.depends('name')
    def _compute_pos_custom_names(self):
        for product in self:
            product.name_en = product.with_context(lang='en_US').name or ''
            product.name_km = product.with_context(lang='km_KH').name or ''
            product.name_cn = product.with_context(lang='zh_CN').name or ''

    @api.model
    def _load_pos_data_fields(self, config):
        fields_to_load = super()._load_pos_data_fields(config)
        for field_name in ['name_en', 'name_km', 'name_cn']:
            if field_name not in fields_to_load:
                fields_to_load.append(field_name)
        return fields_to_load