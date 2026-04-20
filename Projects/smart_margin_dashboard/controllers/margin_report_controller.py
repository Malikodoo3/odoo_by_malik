from odoo import http
from odoo.http import request
import io
import xlsxwriter
import json

class MarginReportController(http.Controller):

    @http.route('/smart_margin_dashboard/download_xlsx', type='http', auth='user', methods=['POST'], csrf=False)
    def download_margin_xlsx(self):
        data = json.loads(request.httprequest.data)
        selected_colors = data.get('selectedColors', [])

        domain = []
        if selected_colors:
            domain.append(['margin_color', 'in', selected_colors])

        margins = request.env['sale.order.margin'].sudo().search(domain, order='id asc')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Margins")

        headers = ["Customer", "Total Revenue", "Total COGS", "Margin", "Margin %"]
        for col, header in enumerate(headers):
            sheet.write(0, col, header)

        for row_idx, margin in enumerate(margins, start=1):
            customer_name = margin.partner_id.name if margin.partner_id else ""
            sheet.write(row_idx, 0, customer_name)
            sheet.write(row_idx, 1, margin.total_revenue or 0)
            sheet.write(row_idx, 2, margin.total_cogs or 0)
            sheet.write(row_idx, 3, margin.net_margin or 0)
            sheet.write(row_idx, 4, margin.margin_percentage or 0)

        workbook.close()
        output.seek(0)

        response = request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename=margin_report.xlsx')
            ]
        )
        return response