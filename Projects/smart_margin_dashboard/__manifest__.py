{
    'name': 'Smart Margin Dashboard',
    'version': '17.0.1.0.0',
    'summary': 'Real-Time Margin Dashboard with Cost Breakdown',
    'author': 'Malik Saffour',
    'category': 'Sales',
    'depends': [
        'sale_management','stock','stock_landed_costs','analytic','sale','mail','base','website','account',
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security_groups.xml",
        "views/res_config_settings_views.xml",
        "views/sale_order_view.xml",
        "views/mail_template.xml",
        "views/margin_card_template.xml",
        "views/margin_card_error.xml",   
        "views/report_margin_pdf.xml",   
        "views/margin_template_pdf.xml",   
    ],
    'assets': {
        'web.assets_frontend': [
        ],
        "web.assets_backend": [
            "smart_margin_dashboard/static/src/margin_report/margin_list/*.*",
            "smart_margin_dashboard/static/src/margin_report/margin_info/*.*",
        ]
    },
    'installable': True,
    'application': False,
}