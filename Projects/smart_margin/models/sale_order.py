# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    
    margin_id = fields.Many2one(
        string='Margin Id',
        comodel_name='sale.order.margin',
        ondelete='set null',
    )
    
    net_margin = fields.Monetary(
        string="Net Margin",
        compute="_compute_margin_fields",
        store=True
    )

    margin_percentage = fields.Float(
        string="Margin %",
        compute="_compute_margin_fields",
        store=True
    )

    margin_color = fields.Selection(
        [
            ('green', 'Green'),
            ('yellow', 'Yellow'),
            ('red', 'Red')
        ],
        compute="_compute_margin_fields",
        store=True
    )
    
    delivery_time = fields.Datetime(
        string= "Delivery Time"
    )
    
    @api.depends(
        'margin_id',
        'margin_id.net_margin',
        'margin_id.margin_percentage',
        'margin_id.margin_color',
        'margin_id.line_ids'
    )
    def _compute_margin_fields(self):
        for order in self:
            margin = order.margin_id

            if margin:
                order.net_margin = margin.net_margin
                order.margin_percentage = margin.margin_percentage
                order.margin_color = margin.margin_color
            else:
                order.net_margin = 0.0
                order.margin_percentage = 0.0
                order.margin_color = False
                
    def action_open_margin(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'smart_margin.action_margin_info',
            'params': {
                'order_id': self.id,
            }
        }
    
    def action_confirm(self):
        _logger.info("Smart Margin: action_confirm triggered")

        res = super().action_confirm()

        for order in self:

            if not order.margin_id:
                margin = self.env['sale.order.margin'].sudo().create({
                    'order_id': order.id,
                })

                # 🔥 force compute
                margin._compute_margin()

                order.margin_id = margin.id

        return res
