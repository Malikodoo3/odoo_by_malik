from odoo import models, fields, api
import logging , base64
_logger = logging.getLogger(__name__)

class SaleOrderMarginWizard(models.TransientModel):
    _name = 'sale.order.margin.wizard'
    _description = 'Sale Order Margin Wizard'

    order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True
    )

    margin_id = fields.Many2one(
        'sale.order.margin',
        string='Margin Record',
        required=True
    )

    line_ids = fields.One2many(
        'sale.order.line.margin',
        'wizard_id',
        string='Lines'
    )

    currency_id = fields.Many2one(
        'res.currency',
        compute='_compute_totals',
        store=True
        
    )

    total_revenue = fields.Monetary(
        string='Total Revenue',
        compute='_compute_totals',
        currency_field='currency_id',
        store=True
    )

    total_cogs = fields.Monetary(
        string='Total COGS',
        compute='_compute_totals',
        currency_field='currency_id',
        store=True
    )

    total_overhead = fields.Monetary(
        string='Total Overhead',
        compute='_compute_totals',
        currency_field='currency_id',
        store=True
    )

    tax_on_company = fields.Monetary(
        string='Total Taxes',
        compute='_compute_totals',
        currency_field='currency_id',
        store=True
    )

    discount_on_company = fields.Monetary(
        string='Total Discount',
        compute='_compute_totals',
        currency_field='currency_id',
        store=True
    )

    net_margin = fields.Monetary(
        string='Net Margin',
        compute='_compute_totals',
        currency_field='currency_id',
        store=True
    )

    margin_percentage = fields.Float(
        string='Margin %',
        compute='_compute_totals',
        store=True
    )

    # -----------------------------
    # COMPUTE TOTALS
    # -----------------------------
    @api.depends('margin_id')
    def _compute_totals(self):
        for wizard in self:
            margin = wizard.order_id.margin_id
            wizard.currency_id = wizard.order_id.currency_id
            if margin:
                wizard.total_revenue = margin.total_revenue
                wizard.total_cogs = margin.total_cogs
                wizard.total_overhead = margin.overhead_amount
                wizard.tax_on_company = margin.tax_on_company
                wizard.discount_on_company = margin.discount_on_company
                wizard.net_margin = margin.net_margin
                wizard.margin_percentage = margin.margin_percentage
            else:
                wizard.currency_id = wizard.order_id.currency_id
                wizard.total_revenue = 0.0
                wizard.total_cogs = 0.0
                wizard.total_overhead = 0.0
                wizard.tax_on_company = 0.0
                wizard.discount_on_company = 0.0
                wizard.net_margin = 0.0
                wizard.margin_percentage = 0.0

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        margin_id = self._context.get('default_margin_id')
        if not margin_id:
            return res

        margin = self.env['sale.order.margin'].sudo().browse(margin_id)

        params = self.env['ir.config_parameter'].sudo()

        overhead_type = params.get_param('smart_margin.overhead_type') or 'percent'
        overhead_value = float(params.get_param('smart_margin.overhead_value') or 0)
        overhead_apply_on = params.get_param('smart_margin.overhead_apply_on') or 'unit'

        lines = []

        for line in margin.order_id.order_line:

            # -------------------
            # Landed Cost
            # -------------------
            landed_cost = line.product_id.standard_price
            line_cogs = landed_cost * line.product_uom_qty

            # -------------------
            # Overhead
            # -------------------
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

            # -------------------
            # Taxes
            # -------------------
            tax = max(line.price_total - line.price_subtotal, 0.0)

            # -------------------
            # Discount
            # -------------------
            discount = getattr(line, 'discount_amount', 0.0)

            # -------------------
            # Line Margin
            # -------------------
            line_margin = line.price_total - (line_cogs + line_overhead + tax + discount)

            lines.append((0, 0, {
                'product_id': line.product_id.id,
                'qty': line.product_uom_qty,
                'unit_price': line.price_unit,
                'landed_cost': landed_cost,
                'overhead': line_overhead,
                'tax_on_company': tax,
                'discount_on_company': discount,
                'line_margin': line_margin,
            }))

        res.update({
            'order_id': margin.order_id.id,
            'margin_id': margin.id,
            'line_ids': lines,
        })

        return res

    def action_generate_margin_pdf_chatter(self):
        """Generate Margin PDF and attach it to Sale Order chatter"""
        self.ensure_one()

        try:
            _logger.info(
                f"📊 Generating Margin PDF for order: {self.order_id.name} (ID: {self.order_id.id})"
            )

            report = self.env.ref(
                "smart_margin_dashboard.action_report_sale_order_margin_wizard_pdf"
            )

            pdf_content, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                report,
                [self.id]
            )

            if not pdf_content:
                _logger.warning(
                    f"⚠️ Empty PDF content for order: {self.order_id.name}"
                )
                return False

            old_attachment = self.env["ir.attachment"].sudo().search([
                ("name", "=", f"Margin-{self.order_id.name}.pdf"),
                ("res_model", "=", "sale.order"),
                ("res_id", "=", self.order_id.id),
            ])

            if old_attachment:
                old_attachment.unlink()

            attachment = self.env["ir.attachment"].sudo().create({
                "name": f"Margin-{self.order_id.name}.pdf",
                "type": "binary",
                "datas": base64.b64encode(pdf_content),
                "res_model": "sale.order",
                "res_id": self.order_id.id,
                "mimetype": "application/pdf",
            })

            self.order_id.message_post(
                body="📊 Margin PDF",
                attachment_ids=[attachment.id],
                subtype_xmlid="mail.mt_note",
            )

            _logger.info(
                f"✅ Margin PDF successfully generated for order: {self.order_id.name}"
            )

            return True

        except Exception as e:
            _logger.error(
                f"❌ Error generating Margin PDF for order {self.order_id.name}: {str(e)}"
            )
            return False

class SaleOrderLineMargin(models.TransientModel):
    _name = 'sale.order.line.margin'
    _description = 'Sale Order Line Margin'

    wizard_id = fields.Many2one('sale.order.margin.wizard', string='Wizard', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Float(string='Sold Qty')
    unit_price = fields.Monetary(string='Unit Price')
    landed_cost = fields.Monetary(string='Landed Cost')
    overhead = fields.Monetary(string='Overhead')
    tax_on_company = fields.Monetary(string='Tax')
    discount_on_company = fields.Monetary(string='Discount')
    line_margin = fields.Monetary(string='Line Margin')
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency', store=True)

    @api.depends('wizard_id')
    def _compute_currency(self):
        for line in self:
            line.currency_id = line.wizard_id.currency_id or self.env.company.currency_id