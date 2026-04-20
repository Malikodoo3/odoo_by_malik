from odoo import models, fields, api
import secrets
import string
import logging
from datetime import datetime, timedelta
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    margin_token = fields.Char(
        string='Margin Token',
    )   
    delivery_time = fields.Datetime(
        string='Delivery Time',
    )   
    expire_margin_portal = fields.Datetime(     
        string='Expire Margin Portal',
        compute='_compute_expire_margin_portal',
        store=True     
    )   
    margin_id = fields.Many2one(
        'sale.order.margin',
        string='Margin Details',
        ondelete='cascade'
    )  
    net_margin = fields.Monetary(
        string='Net Margin',
        compute='_compute_smart_margin',
        store=True,
        currency_field='currency_id',
    )
    margin_percentage = fields.Float(
        string='Margin %',
        compute='_compute_smart_margin',
        store=True,
    )
    @api.depends('margin_id.margin_percentage' , 'margin_id.net_margin')
    def _compute_smart_margin(self):
        for order in self:
           if order.margin_id:
               order.net_margin = order.margin_id.net_margin or 0
               order.margin_percentage = order.margin_id.margin_percentage or 0
    
    # =========================
    # Computed Fields
    # =========================
    @api.depends('delivery_time')
    def _compute_expire_margin_portal(self):
        for rec in self:
            if rec.delivery_time:
                rec.expire_margin_portal = rec.delivery_time
            else:
                rec.expire_margin_portal = fields.Datetime.to_string(
                    datetime.now() + timedelta(days=1)
                )

    def action_open_margin_breakdown(self):
        self.ensure_one()
        return {
            'name': 'Margin Breakdown',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.margin.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_margin_id': self.margin_id.id,
            }
        }
        
    def _generate_margin_token(self):
        self.ensure_one()

        if self.margin_token:
            return
        
        random_code = ''.join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(16)
        )

        self.margin_token = (
            f"{self.id}-{self.partner_id.id}-{random_code}"
        )
    
    def _send_margin_card_in_email(self):
        self.ensure_one()
        partner = self.partner_id
        if not partner or not partner.email:
            _logger.warning(
                "No email found for partner in order %s",
                self.name
            )
            return

        try:
            template = self.env.ref(
                'smart_margin_dashboard.margin_card_email_template'
            ).sudo()

            email_values = {
                'email_to': partner.email,
                'email_from': 'malik.saffour@gmail.com',
            }

            template.send_mail(
                self.id,
                force_send=True,
                email_values=email_values,
            )

            _logger.info(
                "Email sent for order %s",
                self.name
            )
        except Exception as e:
            _logger.error("Email sending failed: %s", e)

    def _generate_margin_card_url(self):
        self.ensure_one()
        for rec in self:
            
            if not rec.margin_token:
                return False

            base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return f"{base_url}/margin/order/{rec.margin_token}"
    # =========================
    # Confirm Override
    # =========================
    def action_confirm(self):
        _logger.info("Malik Override Function 'action_confirm' smart_margin_dashboard\\models\\sale_order.py 🔈🔈🔈🔈")
        res = super().action_confirm()
        for order in self:
            if not order.margin_id:
                margin = self.env['sale.order.margin'].create({
                    'order_id': order.id,
                })

                order.margin_id = margin.id
            order._generate_margin_token()
            order._send_margin_card_in_email()

        return res

# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'
    
#     discount_amount = fields.Monetary(
#         string="Discount Amount",
#         compute="_compute_discount_amount",
#         currency_field='currency_id',
#         store=True
#     )
    
#     @api.depends('product_uom_qty', 'price_unit', 'discount')
#     def _compute_discount_amount(self):
#         for line in self:
#             line.discount_amount = (
#                 line.product_uom_qty
#                 * line.price_unit
#                 * (line.discount / 100.0)
#             )