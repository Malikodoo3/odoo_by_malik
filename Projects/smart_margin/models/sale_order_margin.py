from odoo import models, fields , api


class SaleOrderMargin(models.Model):
    _name = 'sale.order.margin'
    _description = 'Sale Order Margin'
    _rec_name = 'order_id'

    order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
        index=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        compute = '_compute_margin',
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        compute = '_compute_margin',
        store=True
    )

    # 🔹 Totals
    total_revenue = fields.Monetary(
        string="Total Revenue",
        compute = '_compute_margin',
        store=True
    )
    total_cogs = fields.Monetary(
        string="Total COGS",
        compute = '_compute_margin',
        store=True
    )
    overhead_amount = fields.Monetary(
        string="Overhead",
        compute = '_compute_margin',
        store=True
    )

    

    net_margin = fields.Monetary(
        string="Net Margin",
        compute = '_compute_margin',
        store=True
    )
    margin_percentage = fields.Float(
        string="Margin %",
        compute = '_compute_margin',
        store=True
    )

    margin_color = fields.Selection(
        [
            ('green', 'Green'),
            ('yellow', 'Yellow'),
            ('red', 'Red')
        ],
        string='Margin Color',
        compute = '_compute_margin',
        store=True
    )

    # 🔹 Lines
    line_ids = fields.One2many(
        'sale.order.margin.line',
        'margin_id',
        string='Margin Lines',
        compute = '_compute_margin',
        store=True
    )

    @api.depends(
        'order_id',
        'order_id.order_line.price_total',
        'order_id.order_line.product_uom_qty',
        'order_id.order_line.product_id',
        'order_id.order_line.product_id.standard_price',
        'order_id.order_line.move_ids.state',
    )
    def _compute_margin(self):

        params = self.env['ir.config_parameter'].sudo()

        overhead_type = params.get_param('smart_margin.overhead_type', 'percent')
        overhead_value = float(params.get_param('smart_margin.overhead_value') or 0)
        apply_on = params.get_param('smart_margin.overhead_apply_on', 'unit')

        for rec in self:
            order = rec.order_id
            if not order:
                continue

            rec.partner_id = order.partner_id
            rec.currency_id = order.currency_id

            total_revenue = sum(order.order_line.mapped('price_total'))

            landed_map = rec.get_landed_cost(order)

            total_cogs = 0.0
            total_overhead = 0.0
            line_vals = []

            # 🔹 first pass (lines)
            for line in order.order_line:

                revenue = line.price_total
                qty = line.product_uom_qty

                landed_cost = landed_map.get(line.id)
                if not landed_cost:
                    landed_cost = line.product_id.standard_price * qty

                overhead = rec.get_overhead(line, landed_cost, overhead_type, overhead_value, apply_on)

                total_cost = landed_cost + overhead
                margin = revenue - total_cost

                total_cogs += total_cost
                total_overhead += overhead

                line_vals.append({
                    'sale_line_id': line.id,
                    'product_id': line.product_id.id,
                    'qty': qty,
                    'unit_price': line.price_unit,
                    'revenue': revenue,
                    'landed_cost': landed_cost,
                    'overhead_cost': overhead,
                    'total_cost': total_cost,
                    'margin': margin,
                    'currency_id': order.currency_id.id,
                })

            # 🔥 order-level overhead
            if apply_on == 'order':
                if overhead_type == 'fixed':
                    order_overhead = overhead_value
                else:
                    order_overhead = total_cogs * overhead_value / 100

                total_overhead += order_overhead
                total_cogs += order_overhead

            # 🔥 update lines
            rec.create_lines(line_vals)

            # 🔹 totals
            rec.total_revenue = total_revenue
            rec.total_cogs = total_cogs
            rec.overhead_amount = total_overhead
            rec.net_margin = total_revenue - total_cogs

            rec.margin_percentage = (
                (rec.net_margin / total_revenue) * 100
                if total_revenue else 0
            )

            rec.margin_color = rec.select_color()
    
    def get_landed_cost(self, order):
        moves = order.order_line.mapped('move_ids').filtered(lambda m: m.state == 'done')

        valuation_layers = self.env['stock.valuation.layer'].search([
            ('stock_move_id', 'in', moves.ids)
        ])

        landed_map = {}

        for layer in valuation_layers:
            sale_line = layer.stock_move_id.sale_line_id
            if not sale_line:
                continue

            landed_map.setdefault(sale_line.id, 0.0)
            landed_map[sale_line.id] += layer.value

        return landed_map
    
    def get_overhead(self, line, landed_cost, overhead_type, overhead_value, apply_on):

        qty = line.product_uom_qty

        if apply_on == 'unit':
            if overhead_type == 'fixed':
                return overhead_value * qty
            else:
                return landed_cost * overhead_value / 100

        elif apply_on == 'line':
            if overhead_type == 'fixed':
                return overhead_value
            else:
                return landed_cost * overhead_value / 100

        return 0.0  # order handled outside
    
    def create_lines(self, line_vals):
        self.ensure_one()
        self.line_ids = [(5, 0, 0)]
        self.line_ids = [(0, 0, vals) for vals in line_vals]
    
    def select_color(self):

        if self.margin_percentage > 30:
            return 'green'
        elif self.margin_percentage >= 10:
            return 'yellow'
        return 'red'
        
    
class SaleOrderMarginLine(models.Model):
    _name = 'sale.order.margin.line'
    _description = 'Sale Order Margin Line'

    margin_id = fields.Many2one(
        'sale.order.margin',
        string='Margin',
        ondelete='cascade',
        required=True
    )

    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order Line'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )

    qty = fields.Float(string="Quantity")

    unit_price = fields.Monetary(string="Unit Price")
    revenue = fields.Monetary(string="Revenue")

    landed_cost = fields.Monetary(string="Landed Cost")
    overhead_cost = fields.Monetary(string="Overhead")

    tax_amount = fields.Monetary(string="Tax")
    discount_amount = fields.Monetary(string="Discount")

    total_cost = fields.Monetary(string="Total Cost")
    margin = fields.Monetary(string="Margin")

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency'
    )