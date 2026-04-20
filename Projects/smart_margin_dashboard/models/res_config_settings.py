from odoo import models, fields , api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    smart_margin_overhead_type = fields.Selection(
        [('percent', 'Percentage'), ('fixed', 'Fixed')],
        string='Overhead Type',
        config_parameter='smart_margin.overhead_type',
    )

    smart_margin_overhead_value = fields.Float(
        string='Overhead Value',
        config_parameter='smart_margin.overhead_value',
    )

    smart_margin_overhead_apply_on = fields.Selection([
            ('unit', 'Per Unit'),
            ('product', 'Per Product'),
            ('order', 'Per Order')
        ],
        string='Apply Overhead On',
        config_parameter='smart_margin.overhead_apply_on',
    )
    
    def set_values(self):
        res = super().set_values()

        icp = self.env['ir.config_parameter'].sudo()

        icp.set_param('smart_margin.overhead_type', self.smart_margin_overhead_type)
        icp.set_param('smart_margin.overhead_value', self.smart_margin_overhead_value)
        icp.set_param('smart_margin.overhead_apply_on', self.smart_margin_overhead_apply_on)

        margin = self.env['sale.order.margin'].sudo().search([])
        margin._compute_margin()

        return res
    
    @api.model
    def get_values(self):
        res = super().get_values()

        icp = self.env['ir.config_parameter'].sudo()

        res.update(
            smart_margin_overhead_type=icp.get_param('smart_margin.overhead_type', 'percent'),
            smart_margin_overhead_value=float(icp.get_param('smart_margin.overhead_value', 0)),
            smart_margin_overhead_apply_on=icp.get_param('smart_margin.overhead_apply_on', 'unit'),
        )

        return res