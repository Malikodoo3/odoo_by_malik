from odoo import http, fields
from odoo.http import request

class MarginCardController(http.Controller):

    @http.route('/margin/order/<string:margin_token>', type='http', auth='user', website=True)
    def margin_card(self, margin_token, **kw):
        order = request.env['sale.order'].sudo().search([('margin_token', '=', margin_token)], limit=1)
        if not order:
            return request.render('smart_margin_dashboard.margin_card_not_found', {})

        partner = order.partner_id
        
        
        if not order.expire_margin_portal or order.expire_margin_portal < fields.Datetime.now():
            return request.render('smart_margin_dashboard.margin_card_not_found', {})
        
        current_user = request.env.user
        is_margin_manager = current_user.has_group('smart_margin_dashboard.group_margin_manager')        
        
        return request.render('smart_margin_dashboard.margin_card_template', {
            'order': order,
            'partner': partner,
            'is_margin_manager':is_margin_manager
        })