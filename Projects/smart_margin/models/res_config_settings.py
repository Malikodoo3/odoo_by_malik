# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # 🔹 Overhead Type
    smart_margin_overhead_type = fields.Selection(
        [
            ('percent', 'Percentage'),
            ('fixed', 'Fixed')
        ],
        string='Overhead Type',
        config_parameter='smart_margin.overhead_type',
        default='percent'
    )

    # 🔹 Overhead Value
    smart_margin_overhead_value = fields.Float(
        string='Overhead Value',
        config_parameter='smart_margin.overhead_value',
        default=0.0
    )

    # 🔹 Apply On
    smart_margin_overhead_apply_on = fields.Selection(
        [
            ('unit', 'Per Unit'),
            ('line', 'Per Line'),
            ('order', 'Per Order')
        ],
        string='Apply Overhead On',
        config_parameter='smart_margin.overhead_apply_on',
        default='unit'
    )

    @api.model
    def get_values(self):
        res = super().get_values()

        params = self.env['ir.config_parameter'].sudo()

        res.update(
            smart_margin_overhead_type=params.get_param('smart_margin.overhead_type', 'percent'),
            smart_margin_overhead_value=float(params.get_param('smart_margin.overhead_value', 0)),
            smart_margin_overhead_apply_on=params.get_param('smart_margin.overhead_apply_on', 'unit'),
        )
        return res

    def set_values(self):
        res = super().set_values()
        
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('smart_margin.overhead_type', self.smart_margin_overhead_type)
        icp.set_param('smart_margin.overhead_value', self.smart_margin_overhead_value)
        icp.set_param('smart_margin.overhead_apply_on', self.smart_margin_overhead_apply_on)
        
        margins = self.env['sale.order.margin'].sudo().search([])
        margins._compute_margin()

        _logger.info("Smart Margin recomputed after overhead config change")

        return res