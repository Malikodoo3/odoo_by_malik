from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class SaleOrderMargin(models.Model):
    _name = 'sale.order.margin'
    _description = 'Sale Order Margin'

    order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        compute='_compute_margin',
        store=True,
        ondelete='cascade'
    )
    total_revenue = fields.Monetary(
        string="Total Revenue",
        compute='_compute_margin',
        store=True,
        currency_field='currency_id'
    )

    total_cogs = fields.Monetary(
        string="Total COGS",
        compute='_compute_margin',
        store=True,
        currency_field='currency_id'
    )

    overhead_amount = fields.Monetary(
        string="Overhead",
        compute='_compute_margin',
        store=True,
        currency_field='currency_id'
    )

    net_margin = fields.Monetary(
        string="Net Margin",
        compute='_compute_margin',
        store=True,
        currency_field='currency_id'
    )

    margin_percentage = fields.Float(
        string="Margin %",
        compute='_compute_margin',
        digits=(12,2),
        store=True
    )
    
    
    tax_on_company = fields.Monetary(
        string="Tax on Company",
        compute='_compute_margin',
        store=True,
        currency_field='currency_id'
    )

    discount_on_company = fields.Monetary(
        string="Discount on Company",
        compute='_compute_margin',
        store=True,
        currency_field='currency_id'
    )

    margin_color = fields.Selection(
        [
            ('green', 'green'),
            ('yellow', 'yellow'),
            ('red', 'red')
        ],
        string='Margin Color',
        compute='_compute_margin',
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        compute='_compute_currency',
        store=True
    )

    @api.depends('order_id.currency_id')
    def _compute_currency(self):
        for rec in self:
            rec.currency_id = rec.order_id.currency_id

    @api.depends(
        'order_id.order_line.price_total',
        'order_id.order_line.price_subtotal',
        'order_id.order_line.product_uom_qty',
        'order_id.order_line.product_id',
        'order_id.order_line.tax_id',
        'order_id.order_line.discount_amount',
        'order_id.order_line.product_id.standard_price',
    )
    def _compute_margin(self):

        params = self.env['ir.config_parameter'].sudo()
        overhead_type = params.get_param('smart_margin.overhead_type', 'percent')
        overhead_value = float(params.get_param('smart_margin.overhead_value') or 0)
        overhead_apply_on = params.get_param('smart_margin.overhead_apply_on', 'unit')
        _logger.info("Overhead Type: %s", overhead_type)
        _logger.info("Overhead Value: %s", overhead_value)
        _logger.info("Overhead Apply On: %s", overhead_apply_on)

        for rec in self:
            rec.partner_id = rec.order_id.partner_id
            revenue = 0.0
            cogs = 0.0
            total_overhead = 0.0
            total_tax = 0.0
            total_discount = 0.0

            order = rec.order_id

            for line in order.order_line:

                revenue += line.price_total

                layers = self.env['stock.valuation.layer'].search([
                    ('product_id', '=', line.product_id.id),
                    ('stock_move_id', 'in', line.move_ids.filtered(lambda m: m.state == 'done').ids)
                ])

                landed_cost = sum(l.value for l in layers) or line.product_id.standard_price
                line_cogs = landed_cost

                line_overhead = 0.0

                if overhead_apply_on == 'unit':
                    if overhead_type == 'fixed':
                        line_overhead = overhead_value * line.product_uom_qty
                    else:
                        line_overhead = line_cogs * overhead_value / 100

                elif overhead_apply_on == 'product':
                    if overhead_type == 'fixed':
                        line_overhead = overhead_value
                    else:
                        line_overhead = line_cogs * overhead_value / 100

                total_overhead += line_overhead

                tax_amount = max(line.price_total - line.price_subtotal, 0.0)
                total_tax += tax_amount

                discount_amount = getattr(line, 'discount_amount', 0.0)
                total_discount += discount_amount

                line_total_cogs = line_cogs + line_overhead + tax_amount + discount_amount
                cogs += line_total_cogs

            if overhead_apply_on == 'order':
                if overhead_type == 'fixed':
                    order_overhead = overhead_value
                else:
                    order_overhead = cogs * overhead_value / 100

                total_overhead += order_overhead
                cogs += order_overhead

            rec.total_revenue = revenue
            rec.total_cogs = cogs
            rec.overhead_amount = total_overhead
            rec.tax_on_company = total_tax
            rec.discount_on_company = total_discount
            rec.net_margin = revenue - cogs

            rec.margin_percentage = (rec.net_margin / revenue * 100) if revenue else 0

            if rec.margin_percentage > 30:
                rec.margin_color = 'green'
            elif 10 <= rec.margin_percentage <= 30:
                rec.margin_color = 'yellow'
            else:
                rec.margin_color = 'red'